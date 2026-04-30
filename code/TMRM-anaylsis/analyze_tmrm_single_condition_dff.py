"""Compute and plot DeltaF/F0 traces for one TMRM condition.

Supported input:
    data/time-series/tmrm/<condition>.parquet

Generated output:
    outputs/tmrm/<condition>/cell_detections_dff.csv
    outputs/tmrm/<condition>/single_cell_dff_traces.png
    outputs/tmrm/<condition>/population_dff_mean_sem.png

The upstream image segmentation and fluorescence extraction workflow is not
included in this repository. This script starts from the curated time-series
tables committed under data/time-series/tmrm.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_FILE = ROOT / "data" / "time-series" / "tmrm" / "200mM.parquet"
DEFAULT_OUTPUT_ROOT = ROOT / "outputs" / "tmrm"
DEFAULT_SHOCK_FRAME = 35
DEFAULT_BASELINE_WINDOW = 10
DEFAULT_FRAME_INTERVAL_S = 5
DEFAULT_YMIN = -0.03
DEFAULT_YMAX = 0.015


def compute_dff(
    df: pd.DataFrame, shock_frame: int, baseline_window: int
) -> pd.DataFrame:
    """Compute DeltaF/F0 per track_id from curated TMRM fluorescence traces."""
    df = df[df["track_id"] >= 0].copy()
    df["dff"] = np.nan

    for _track_id, group in df.groupby("track_id"):
        group = group.sort_values("frame")
        baseline = group[
            (group["frame"] < shock_frame)
            & (group["frame"] >= shock_frame - baseline_window)
        ]
        if len(baseline) < 3:
            continue

        f0 = baseline["fluorescence"].mean()
        df.loc[group.index, "dff"] = (group["fluorescence"] - f0) / (f0 - 1)

    return df


def plot_dff(
    df: pd.DataFrame,
    out_dir: Path,
    exp_name: str,
    y_limits: tuple[float, float],
) -> None:
    """Save single-cell and population DeltaF/F0 plots."""
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure()
    for track_id, group in df.groupby("track_id"):
        if track_id >= 0 and group["dff"].notna().any():
            plt.plot(group["time_s"], group["dff"], alpha=0.4)

    plt.axhline(0, color="k", lw=1)
    plt.xlabel("Time (s)")
    plt.ylabel("DeltaF/F0")
    plt.title(f"{exp_name} - Single-cell DeltaF/F0 traces")
    plt.ylim(*y_limits)
    plt.tight_layout()
    plt.savefig(out_dir / "single_cell_dff_traces.png", dpi=300)
    plt.close()

    pop = df.groupby("time_s")["dff"].agg(["mean", "sem"]).reset_index()
    plt.figure()
    plt.plot(pop["time_s"], pop["mean"], label="Mean DeltaF/F0")
    plt.fill_between(
        pop["time_s"],
        pop["mean"] - pop["sem"],
        pop["mean"] + pop["sem"],
        alpha=0.3,
    )
    plt.axhline(0, color="k", lw=1)
    plt.xlabel("Time (s)")
    plt.ylabel("DeltaF/F0")
    plt.title(f"{exp_name} - Population DeltaF/F0 (mean +/- SEM)")
    plt.ylim(-0.5, 0.1)
    plt.tight_layout()
    plt.savefig(out_dir / "population_dff_mean_sem.png", dpi=300)
    plt.close()


def run_analysis(
    input_file: Path,
    output_root: Path,
    shock_frame: int,
    baseline_window: int,
    frame_interval_s: float,
    y_limits: tuple[float, float],
) -> None:
    df = pd.read_parquet(input_file)
    df["time_s"] = df["frame"] * frame_interval_s
    exp_name = input_file.stem
    out_dir = output_root / exp_name
    out_dir.mkdir(parents=True, exist_ok=True)

    df_dff = compute_dff(df, shock_frame, baseline_window)
    df_dff.to_csv(out_dir / "cell_detections_dff.csv", index=False)
    plot_dff(df_dff, out_dir, exp_name, y_limits)

    print("TMRM DeltaF/F0 analysis complete.")
    print(f"Outputs saved in: {out_dir}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT_FILE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--shock-frame", type=int, default=DEFAULT_SHOCK_FRAME)
    parser.add_argument("--baseline-window", type=int, default=DEFAULT_BASELINE_WINDOW)
    parser.add_argument("--frame-interval-s", type=float, default=DEFAULT_FRAME_INTERVAL_S)
    parser.add_argument("--ymin", type=float, default=DEFAULT_YMIN)
    parser.add_argument("--ymax", type=float, default=DEFAULT_YMAX)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_analysis(
        input_file=args.input_file,
        output_root=args.output_root,
        shock_frame=args.shock_frame,
        baseline_window=args.baseline_window,
        frame_interval_s=args.frame_interval_s,
        y_limits=(args.ymin, args.ymax),
    )


if __name__ == "__main__":
    main()
