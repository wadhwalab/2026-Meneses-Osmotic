"""Plot measured motor speed with an expected viscosity-only speed drop.

Supported input:
    data/time-series/bead/*.parquet, materialized through bead_time_series.py

Generated output:
    outputs/figure-panels/supplement-clockwise-viscosity-control.pdf
    outputs/bead/viscosity-cw/time_to_reach_y_range.txt

The upstream bead tracking and rotation-frequency extraction workflow is not
included in this repository. This script starts from the curated bead
time-series tables committed under data/time-series/bead.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from bead_time_series import ROOT, legacy_condition_folder, read_legacy_speed_csv


DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "bead" / "viscosity-cw"
DEFAULT_FIGURE_DIR = ROOT / "outputs" / "figure-panels"
DEFAULT_FIGURE_NAME = "supplement-clockwise-viscosity-control.pdf"


def calculate_time_to_reach_y_range_and_plot(
    folder_path: Path,
    y_drop: float,
    drop_x: float,
    return_x: float,
    output_file: Path,
    plot_file: Path,
) -> None:
    plot_file.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 5.5))
    ax = plt.gca()
    plt.rcParams.update({"font.size": 25})
    plt.rcParams["font.family"] = "Arial"
    for spine in ax.spines.values():
        spine.set_linewidth(2)

    max_time = 380
    plotted = False

    for file_path in sorted(folder_path.glob("*.csv")):
        try:
            df = read_legacy_speed_csv(file_path)
            time_s = df["frame"].to_numpy(dtype=float) / 300
            speed = df["frequency_hz"].to_numpy(dtype=float)
            baseline = np.nanmean(speed[time_s < drop_x])
            if not np.isfinite(baseline) or baseline == 0:
                continue

            speed = speed / baseline
            max_time = max(max_time, float(np.nanmax(time_s)))
            ax.plot(time_s, speed, label="Measured \nmotor speed", color="Red")
            plotted = True
        except Exception as exc:
            print(f"Error reading {file_path}: {exc}")

    if not plotted:
        raise FileNotFoundError(f"No usable trace CSV files found in {folder_path}")

    # This dashed reference is the motor speed expected if viscosity were the
    # only reason the bead slowed down during the shock.
    x_values = [0, drop_x, drop_x, return_x, return_x, max_time]
    y_values = [1, 1, y_drop, y_drop, 1, 1]
    ax.plot(
        x_values,
        y_values,
        linestyle="--",
        color="Black",
        linewidth=2.5,
        label="Speed \ndecrease due \nto change in \nviscosity",
    )

    ax.set_ylim(-0.05, 1.25)
    ax.set_xlim(0, 380)
    ax.tick_params(axis="both", which="major", labelsize=25, width=2, length=7.5, pad=8)
    ax.set_xlabel("Time (s)", fontsize=25)
    ax.set_ylabel("Rotation Speed (Normalized)", fontsize=25)
    ax.tick_params(which="both", direction="in")
    ax.axvspan(180, 270, color="lightgray", alpha=1)
    ax.legend(loc="lower left", fontsize=25, frameon=False)
    ax.set_xticks(np.arange(0, 381, 50))
    ax.set_yticks(np.arange(0, 1.26, 0.25)[:-1])

    plt.savefig(plot_file, format="pdf", dpi=350)
    output_file.write_text(
        (
            f"A dotted line starts at y = 1, drops to y = {y_drop} at "
            f"x = {drop_x}, and returns to y = 1 at x = {return_x}.\n"
        ),
        encoding="utf-8",
    )

    print(f"Result saved to {output_file}")
    print(f"Plot saved to {plot_file}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assay", default="Clockwise")
    parser.add_argument("--condition-mm", default="500")
    parser.add_argument("--y-drop", type=float, default=0.57)
    parser.add_argument("--drop-x", type=float, default=180)
    parser.add_argument("--return-x", type=float, default=270)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    parser.add_argument("--figure-name", default=DEFAULT_FIGURE_NAME)
    parser.add_argument("--show", action="store_true", help="Display the plot window.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    folder_path = legacy_condition_folder(
        assay=args.assay, condition_mM=args.condition_mm
    )
    output_file = args.output_dir / "time_to_reach_y_range.txt"
    calculate_time_to_reach_y_range_and_plot(
        folder_path=folder_path,
        y_drop=args.y_drop,
        drop_x=args.drop_x,
        return_x=args.return_x,
        output_file=output_file,
        plot_file=args.figure_dir / args.figure_name,
    )
    if args.show:
        plt.show()
    else:
        plt.close("all")


if __name__ == "__main__":
    main()
