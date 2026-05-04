"""Plot measured motor speed with an expected viscosity-only speed drop.

Supported input:
    data/time-series/bead/*.parquet, materialized through bead_time_series.py

Generated output:
    outputs/figure-panels/supplement-sorbitol-viscosity.pdf
    outputs/bead/viscosity-sorb/time_to_reach_y_range.txt

The upstream bead tracking and rotation-frequency extraction workflow is not
included in this repository. This script starts from the curated bead
time-series tables committed under data/time-series/bead.
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from bead_time_series import ROOT, iter_condition_traces


# Default folders and file name used when no command-line overrides are given.
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "bead" / "viscosity-sorb"
DEFAULT_FIGURE_DIR = ROOT / "outputs" / "figure-panels"
DEFAULT_FIGURE_NAME = "supplement-sorbitol-viscosity.pdf"


def calculate_time_to_reach_y_range_and_plot(
    assay: str,
    condition_mM: str | int,
    y_drop: float,
    drop_x: float,
    return_x: float,
    output_file: Path,
    plot_file: Path,
) -> None:
    """Build the viscosity-control figure and save a short text summary.

    This function reads bead traces for one assay/condition, normalizes each
    trace to its own pre-shock baseline, averages across traces, and compares
    the measured mean response to an idealized viscosity-only reference line.
    """

    # Ensure the figure output folder exists before we try to save.
    plot_file.parent.mkdir(parents=True, exist_ok=True)

    # Create a fresh figure and axis for plotting.
    plt.figure(figsize=(10, 5.5))
    ax = plt.gca()

    # Global style choices for readability in manuscript figures.
    plt.rcParams.update({"font.size": 25})
    plt.rcParams["font.family"] = "Arial"

    # Thicken the frame lines (spines) around the plot.
    for spine in ax.spines.values():
        spine.set_linewidth(2)

    # Common time grid so all traces can be compared point-by-point.
    common_time = np.arange(0, 380.05, 0.1)

    # We will store each normalized trace in this list.
    normalized: list[np.ndarray] = []

    # Loop through all traces for the selected assay and osmotic condition.
    for _, trace in iter_condition_traces(assay=assay, condition_mM=condition_mM):
        # Extract time and rotation speed as numeric arrays.
        time_s = trace["time_s"].to_numpy(dtype=float)
        speed = trace["frequency_hz"].to_numpy(dtype=float)

        # Baseline = mean speed before the drop starts (time < drop_x).
        baseline = np.nanmean(speed[time_s < drop_x])

        # Skip traces with invalid or zero baseline (cannot normalize safely).
        if not np.isfinite(baseline) or baseline == 0:
            continue

        # Interpolate onto the common time axis after baseline normalization.
        # left/right = NaN avoids inventing data outside measured time range.
        normalized.append(
            np.interp(common_time, time_s, speed / baseline, left=np.nan, right=np.nan)
        )

    # Stop with a clear message if no usable traces were found.
    if not normalized:
        raise FileNotFoundError(f"No usable traces found for {assay} {condition_mM} mM")

    # Stack traces into a 2D matrix: rows = cells/traces, columns = time points.
    matrix = np.vstack(normalized)

    # Compute mean at each time point (ignoring NaN values).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mean = np.nanmean(matrix, axis=0)

    # Plot measured mean normalized speed.
    ax.plot(common_time, mean, color="Blue", linewidth=1, label="Measured \nmotor speed")

    # This dashed reference is the motor speed expected if viscosity were the
    # only reason the bead slowed down during the shock.
    x_values = [0, drop_x, drop_x, return_x, return_x, common_time[-1]]
    y_values = [1, 1, y_drop, y_drop, 1, 1]
    ax.plot(
        x_values,
        y_values,
        linestyle="--",
        color="Black",
        linewidth=2.5,
        label="Speed \ndecrease due \nto change in \nviscosity",
    )

    # Axis limits and style settings.
    ax.set_ylim(-0.05, 1.25)
    ax.set_xlim(0, 380)
    ax.tick_params(axis="both", which="major", labelsize=25, width=2, length=7.5, pad=8)
    ax.set_xlabel("Time (s)", fontsize=25)
    ax.set_ylabel("Rotation Speed (Normalized)", fontsize=25)
    ax.tick_params(which="both", direction="in")

    # Shade the interval when shock media is present.
    ax.axvspan(180, 270, color="lightgray", alpha=1)

    # Legend and explicit tick locations for consistent panel formatting.
    ax.legend(loc="lower left", fontsize=25, frameon=False)
    ax.set_xticks(np.arange(0, 381, 50))
    ax.set_yticks(np.arange(0, 1.26, 0.25)[:-1])

    # Save the figure
    plt.savefig(plot_file, format="pdf", dpi=350)

    # Save a simple plain-text description of the reference line used.
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
    """Define command-line options so users can run this script flexibly."""

    # The parser reads flags such as --assay and --condition-mm from terminal.
    parser = argparse.ArgumentParser(description=__doc__)

    # Biological/experimental inputs.
    parser.add_argument("--assay", default="Sorbitol")
    parser.add_argument("--condition-mm", default="200")

    # Reference-line geometry for the expected viscosity-only response.
    parser.add_argument("--y-drop", type=float, default=0.86)
    parser.add_argument("--drop-x", type=float, default=180)
    parser.add_argument("--return-x", type=float, default=270)

    # Output locations and file naming.
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    parser.add_argument("--figure-name", default=DEFAULT_FIGURE_NAME)

    # Optional interactive display (mainly useful during local exploration).
    parser.add_argument("--show", action="store_true", help="Display the plot window.")
    return parser


def main() -> None:
    """Parse user inputs, run analysis, and either show or close the figure."""

    # Read command-line arguments.
    args = build_parser().parse_args()

    # Build and create output folder for the text summary.
    output_file = args.output_dir / "time_to_reach_y_range.txt"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Run the main analysis + plotting routine.
    calculate_time_to_reach_y_range_and_plot(
        assay=args.assay,
        condition_mM=args.condition_mm,
        y_drop=args.y_drop,
        drop_x=args.drop_x,
        return_x=args.return_x,
        output_file=output_file,
        plot_file=args.figure_dir / args.figure_name,
    )

    # Show an interactive window only if user asked for it.
    if args.show:
        plt.show()
    else:
        # Close all figure objects in non-interactive/batch mode.
        plt.close("all")


# Standard Python entry point.
if __name__ == "__main__":
    main()
