# -*- coding: utf-8 -*-
"""
Created on Tue Jan 20 14:20:57 2026

@author: fjavi
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
from pathlib import Path

# ================= USER PARAMETERS =================
ROOT = Path(__file__).resolve().parents[2]
folder_path = ROOT / "data" / "time-series" / "cell-area"  # <--- FOLDER containing all CSVs
output_folder = ROOT / "outputs" / "cell-area"
shock_frame = 35  # frame index of shock
baseline_window = 10  # frames before shock for F0
frame_interval_s = 5  # seconds per frame

# y-axis limits
Low_Lim = -0.25
Hi_Lim = 0.10


# ===================================================
def filename_to_label(fname):
    """
    Convert a CSV filename to a human-readable label used in the legend.
    Examples:
      '300csv_LONG_Cell_Areas_DoG_Otsu.csv' -> '300 mM'
      'Controlcsv_LONG_Cell_Areas_DoG_Otsu.csv' -> 'Control'
    """
    b = os.path.basename(fname)
    b_noext = os.path.splitext(b)[0]

    # Control case
    if b_noext.lower().startswith("control"):
        return "Control"

    # Extract first 2-4 digit number (e.g. 200, 300, 1000)
    m = re.search(r"(\d{2,4})", b_noext)
    if m:
        return f"{m.group(1)} mM"

    # Fallback: cleaned basename
    return b_noext


def sort_key_control_first(fname):
    """
    Sorting key:
      - Control first
      - then numeric concentrations in ascending order
      - anything unexpected last
    Returns a tuple so sorting is deterministic.
    """
    b = os.path.basename(fname).lower()

    if b.startswith("control"):
        return (0, 0)  # Control always first

    m = re.search(r"(\d{2,4})", b)
    if m:
        return (1, int(m.group(1)))  # Then by concentration number

    return (2, float("inf"))  # Anything unexpected last


# ====================================================


def compute_dff(df, shock_frame, baseline_window):
    """
    Compute ΔF/F₀ per track_id.
    F₀ is the mean area over the pre-shock baseline window.
    """
    # keep only valid tracks
    df = df[df["track_id"] >= 0].copy()

    # initialize dff column
    df["dff"] = np.nan

    for track_id, g in df.groupby("track_id"):
        g = g.sort_values("frame")

        baseline = g[
            (g["frame"] < shock_frame) & (g["frame"] >= shock_frame - baseline_window)
        ]

        # need at least a few points to define baseline
        if len(baseline) < 3:
            continue

        F0 = baseline["area"].mean()
        df.loc[g.index, "dff"] = (g["area"] - F0) / F0

    return df


def compute_population_stats(df):
    """
    From a dataframe with columns time_s and dff,
    return a dataframe with columns: time_s, mean, sem
    """
    pop = df.groupby("time_s")["dff"].agg(["mean", "sem"]).reset_index()
    return pop


def plot_multi_population(pop_list, labels, out_path):
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

    ax.axvspan(180, 270, color="lightgray", alpha=0.6)
    ax.set_xlabel("Time (s)", fontsize=25)
    ax.set_ylabel("ΔA/A₀", fontsize=25)
    ticks = np.arange(-0.20, 0.10, 0.05)
    ax.set_yticks(ticks[:-1])
    ax.set_ylim(-0.20, 0.04)
    ax.set_xticks(np.arange(0, 381, 50))
    ax.set_xlim(0, 380)

    ax.legend(frameon=False, fontsize=25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


# ================= MAIN SCRIPT =================

# find all CSV files in the folder (exclude any *_dff.csv files created by previous runs)
all_csv = glob.glob(os.path.join(folder_path, "*.csv"))
csv_files = [f for f in all_csv if not os.path.basename(f).endswith("_dff.csv")]

# Sort: Control first, then increasing concentration
csv_files = sorted(csv_files, key=sort_key_control_first)

# sanity checks
if not csv_files:
    raise FileNotFoundError(f"No CSV files found in folder: {folder_path}")

pop_list = []
labels = []

for i, csv_path in enumerate(csv_files):
    print(f"Processing {csv_path}")

    df = pd.read_csv(csv_path)
    df["time_s"] = df["frame"] * frame_interval_s
    df_dff = compute_dff(df, shock_frame, baseline_window)

    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    out_dir = output_folder / "dff"
    os.makedirs(out_dir, exist_ok=True)
    dff_csv_path = os.path.join(out_dir, f"{base_name}_dff.csv")
    df_dff.to_csv(dff_csv_path, index=False)

    pop = compute_population_stats(df_dff)
    pop_list.append(pop)

    # <-- manual legend label here
    labels.append(filename_to_label(csv_path))

# name for the combined figure
os.makedirs(output_folder, exist_ok=True)
folder_name = os.path.basename(os.path.normpath(folder_path))
combined_plot_path1 = os.path.join(
    output_folder, f"{folder_name}_population_dff_multi.pdf"
)


# make one combined population plot
plot_multi_population(pop_list, labels, combined_plot_path1)

print("ΔF/F₀ multi-file analysis complete.")
print("Per-file ΔF/F₀ CSVs saved as <originalname>_dff.csv")
