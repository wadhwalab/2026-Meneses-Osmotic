import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ================= USER PARAMETERS =================
ROOT = Path(__file__).resolve().parents[2]
csv_path = ROOT / "data" / "time-series" / "tmrm" / "200mM.csv"
shock_frame = 35  # <-- SET THIS
baseline_window = 10  # frames before shock
frame_interval_s = 5  # seconds per frame

# y-axis limits
Low_Lim = -0.03
Hi_Lim = 0.015
# ===================================================


def compute_dff(df, shock_frame, baseline_window):
    """
    Compute ΔF/F₀ per track_id.
    F₀ is the mean fluorescence over the pre-shock baseline window.
    """
    df = df[df["track_id"] >= 0].copy()
    df["dff"] = np.nan

    for track_id, g in df.groupby("track_id"):
        g = g.sort_values("frame")

        baseline = g[
            (g["frame"] < shock_frame) & (g["frame"] >= shock_frame - baseline_window)
        ]

        if len(baseline) < 3:
            continue

        F0 = baseline["fluorescence"].mean()
        df.loc[g.index, "dff"] = (g["fluorescence"] - F0) / (F0 - 1)

    return df


def plot_dff(df, out_dir):
    """Save ΔF/F₀ plots."""
    # ---- Single-cell traces ----
    plt.figure()
    for tid, g in df.groupby("track_id"):
        if tid >= 0 and g["dff"].notna().any():
            plt.plot(g["time_s"], g["dff"], alpha=0.4)

    plt.axhline(0, color="k", lw=1)
    # plt.axvline(shock_frame * frame_interval_s, color="r", ls="--", label="Shock")
    plt.xlabel("Time (s)")
    plt.ylabel("ΔF/F₀")
    plt.title(f"{exp_name} – Single-cell ΔF/F₀ traces")
    plt.ylim(Low_Lim, Hi_Lim)  # The limit of y axis
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "single_cell_dff_traces.png"), dpi=300)
    plt.close()

    # ---- Population mean ± SEM ---- % SEM = Standard Error of Mean
    pop = (
        df.groupby("time_s")["dff"].agg(["mean", "sem"]).reset_index()
    )  # Calculates the MEAN and SEM

    plt.figure()
    plt.plot(pop["time_s"], pop["mean"], label="Mean ΔF/F₀")  # plots the MEAN line
    plt.fill_between(
        pop["time_s"],
        pop["mean"] - pop["sem"],
        pop["mean"] + pop["sem"],
        alpha=0.3,  # alpha makes the SEM transparent dim
    )

    plt.axhline(0, color="k", lw=1)
    # plt.axvline(shock_frame * frame_interval_s, color="r", ls="--")
    plt.xlabel("Time (s)")
    plt.ylabel("ΔF/F₀")
    plt.title(f"{exp_name} – Population ΔF/F₀ (mean ± SEM)")
    plt.ylim(-0.5, 0.1)  # The limit of y axis
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "population_dff_mean_sem.png"), dpi=300)
    plt.close()


# ================= MAIN SCRIPT =================

df = pd.read_csv(csv_path)
df["time_s"] = df["frame"] * frame_interval_s
out_dir = ROOT / "outputs" / "tmrm" / Path(csv_path).stem
os.makedirs(out_dir, exist_ok=True)
exp_name = Path(csv_path).stem

df_dff = compute_dff(df, shock_frame, baseline_window)

# Save new CSV
df_dff.to_csv(os.path.join(out_dir, "cell_detections_dff_019_.csv"), index=False)

# Make plots
plot_dff(df_dff, out_dir)

print("ΔF/F₀ analysis complete.")
print("Saved:")
print(" - cell_detections_dff.csv")
print(" - single_cell_dff_traces.png")
print(" - population_dff_mean_sem.png")
