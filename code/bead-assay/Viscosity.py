import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from bead_time_series import ROOT, legacy_condition_folder


def calculate_time_to_reach_y_range_and_plot(
    folder_path, y_drop, drop_x, return_x, output_file, plot_folder
):
    # Ensure the plot folder exists
    os.makedirs(plot_folder, exist_ok=True)
    plot_file = os.path.join(plot_folder, "plot.pdf")

    # Create a plot
    plt.figure(figsize=(10, 5.5))
    ax = plt.gca()
    plt.rcParams.update({"font.size": 25})
    plt.rcParams["font.family"] = "Arial"
    # Set border thickness
    for spine in ax.spines.values():
        spine.set_linewidth(2)

    # Loop through all CSV files in the given folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            file_path = os.path.join(folder_path, file_name)
            try:
                df = pd.read_csv(file_path, header=None)
                df[0] = pd.to_numeric(df[0], errors="coerce")
                df[1] = pd.to_numeric(df[1], errors="coerce")
                df = df.dropna(subset=[0, 1])
                ax.plot(
                    df[0],
                    df[1],
                    label=f"Measured \nmotor speed",
                    color="Red",
                )
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # Add the dotted line: constant at 1 before `drop_x` and after `return_x`, with a drop at `y_drop`
    x_values = [0, drop_x, drop_x, return_x, return_x, max(df[0])]
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

    # Custom ticks
    ax.set_xticks(np.arange(0, 381, 50))  # Set x-ticks every 50
    ticks = np.arange(0, 1.26, 0.25)
    ax.set_yticks(ticks[:-1])  # Remove the last tick (1.25)

    # Save the plot as PDF in the specified folder
    plt.savefig(plot_file, format="pdf", dpi=350)

    # Write the result to a text file
    with open(output_file, "w") as f:
        f.write(
            f"A dotted line starts at y = 1, drops to y = {y_drop} at x = {drop_x}, and returns to y = 1 at x = {return_x}.\n"
        )

    print(f"Result saved to {output_file}")
    print(f"Plot saved to {plot_file}")


# Example using compact canonical bead time series.
folder_path = legacy_condition_folder(assay="Clockwise", condition_mM=500)
y_drop = 0.57
drop_x = 180
return_x = 270
plot_folder = ROOT / "outputs" / "bead" / "viscosity-cw"
output_file = plot_folder / "time_to_reach_y_range.txt"

calculate_time_to_reach_y_range_and_plot(
    folder_path, y_drop, drop_x, return_x, output_file, plot_folder
)
# Show the plot
plt.show()
