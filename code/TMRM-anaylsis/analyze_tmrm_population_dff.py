"""Compute per-track and population TMRM DeltaF/F0 traces.

Supported input:
    data/time-series/tmrm/*.parquet

Generated output:
    outputs/tmrm/dff/*_dff.csv
    outputs/figure-panels/figure-2b-tmrm-population.pdf

The upstream image segmentation and fluorescence extraction workflow is not
included in this repository. This script starts from the curated time-series
tables committed under data/time-series/tmrm.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = ROOT / "data" / "time-series" / "tmrm"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "tmrm"
DEFAULT_FIGURE_DIR = ROOT / "outputs" / "figure-panels"
DEFAULT_FIGURE_NAME = "figure-2b-tmrm-population.pdf"
DEFAULT_SHOCK_FRAME = 35
DEFAULT_BASELINE_WINDOW = 10
DEFAULT_FRAME_INTERVAL_S = 5


def filename_to_label(path: str | Path) -> str:
    """Convert an input filename to the label used in the plot legend."""
    stem = Path(path).stem
    if stem.lower().startswith("control"):
        return "Control"

    match = re.search(r"(\d{2,4})", stem)
    if match:
        return f"{match.group(1)} mM"

    return stem


def sort_key_control_first(path: str | Path) -> tuple[int, int]:
    """Sort control first, then numeric concentrations in ascending order."""
    name = Path(path).name.lower()
    if name.startswith("control"):
        return (0, 0)

    match = re.search(r"(\d{2,4})", name)
    if match:
        return (1, int(match.group(1)))

    return (2, 10**9)


def compute_dff(
    df: pd.DataFrame, shock_frame: int, baseline_window: int
) -> pd.DataFrame:
    """Compute DeltaF/F0 per track_id from curated TMRM fluorescence traces."""
    df = df[df["track_id"] >= 0].copy()
    df["dff"] = np.nan

    for _track_id, group in df.groupby("track_id"):
        group = group.sort_values("frame")
        # Use each cell's own pre-shock fluorescence as its reference point.
        baseline = group[
            (group["frame"] < shock_frame)
            & (group["frame"] >= shock_frame - baseline_window)
        ]
        if len(baseline) < 3:
            continue

        f0 = baseline["fluorescence"].mean()
        # The input is already a cell/background ratio near 1, so normalize
        # the shock response relative to the signal above background.
        df.loc[group.index, "dff"] = (group["fluorescence"] - f0) / (f0 - 1)

    return df


def compute_population_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Return mean and SEM DeltaF/F0 values grouped by time."""
    return df.groupby("time_s")["dff"].agg(["mean", "sem"]).reset_index()


def plot_multi_population(
    pop_list: list[pd.DataFrame], labels: list[str], out_path: Path
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.75))

    plt.rcParams.update({"font.size": 25})
    plt.rcParams["font.family"] = "Arial"

    for side in ["top", "bottom", "left", "right"]:
        ax.spines[side].set_linewidth(2)

    ax.tick_params(axis="x", direction="in", width=2, length=7.5, pad=8, labelsize=25)
    ax.tick_params(axis="y", direction="in", width=2, length=7.5, pad=8, labelsize=25)

    for pop, label in zip(pop_list, labels):
        if pop["mean"].isna().all():
            continue

        ax.plot(pop["time_s"], pop["mean"], label=label)
        ax.fill_between(
            pop["time_s"],
            pop["mean"] - pop["sem"],
            pop["mean"] + pop["sem"],
            alpha=0.3,
        )

    ax.axvspan(180, 265, color="lightgray", alpha=0.6)
    ax.set_xlabel("Time (s)", fontsize=25)
    ax.set_ylabel("ΔF/F₀", fontsize=25)
    ticks = np.arange(-0.20, 0.10, 0.05)
    ax.set_yticks(ticks[:-1])
    ax.set_ylim(-0.20, 0.04)
    ax.set_xticks(np.arange(0, 381, 50))
    ax.set_xlim(0, 380)

    ax.legend(frameon=False, loc="lower left", fontsize=25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=350)
    plt.close(fig)


def run_analysis(
    input_dir: Path,
    output_dir: Path,
    figure_dir: Path,
    figure_name: str,
    shock_frame: int,
    baseline_window: int,
    frame_interval_s: float,
) -> None:
    data_files = sorted(input_dir.glob("*.parquet"), key=sort_key_control_first)
    if not data_files:
        raise FileNotFoundError(f"No Parquet files found in folder: {input_dir}")

    pop_list: list[pd.DataFrame] = []
    labels: list[str] = []
    dff_dir = output_dir / "dff"
    dff_dir.mkdir(parents=True, exist_ok=True)

    for data_path in data_files:
        print(f"Processing {data_path}")
        df = pd.read_parquet(data_path)
        df["time_s"] = df["frame"] * frame_interval_s
        df_dff = compute_dff(df, shock_frame, baseline_window)

        df_dff.to_csv(dff_dir / f"{data_path.stem}_dff.csv", index=False)
        pop_list.append(compute_population_stats(df_dff))
        labels.append(filename_to_label(data_path))

    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    combined_plot_path = figure_dir / figure_name
    plot_multi_population(pop_list, labels, combined_plot_path)

    print("TMRM DeltaF/F0 multi-file analysis complete.")
    print(f"Per-file CSVs saved in: {dff_dir}")
    print(f"Population plot saved to: {combined_plot_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    parser.add_argument("--figure-name", default=DEFAULT_FIGURE_NAME)
    parser.add_argument("--shock-frame", type=int, default=DEFAULT_SHOCK_FRAME)
    parser.add_argument("--baseline-window", type=int, default=DEFAULT_BASELINE_WINDOW)
    parser.add_argument("--frame-interval-s", type=float, default=DEFAULT_FRAME_INTERVAL_S)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_analysis(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        figure_dir=args.figure_dir,
        figure_name=args.figure_name,
        shock_frame=args.shock_frame,
        baseline_window=args.baseline_window,
        frame_interval_s=args.frame_interval_s,
    )


if __name__ == "__main__":
    main()
