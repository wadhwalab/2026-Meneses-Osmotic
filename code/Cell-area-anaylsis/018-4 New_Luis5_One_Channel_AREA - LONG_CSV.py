# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 17:23:38 2026

@author: fjavi
"""

# -*- coding: utf-8 -*-
"""
Integrated pipeline: whole ND2 video processed with DoG+Otsu+close+fill_holes segmentation.
- Uses single (phase) channel only.
- Adds a maximum-area guard (fraction of ROI area).
- Saves both wide CSV and LONG CSV (track_id, frame, value) for areas.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches
from nd2reader import ND2Reader
import pandas as pd
from scipy import ndimage

# ---------------- USER TUNABLE PARAMETERS ------------------------------------
# File / folder settings (edit)

folder_path = r"C:\Users\lemenese\ASU Dropbox\KE-TF Biodesign ME Wadhwa\Wadhwa Lab\Luis_M\Osmotic-shock-motor-response-project-2022-2025\Data\Cell-area"
file_name = "change-in-area-control.nd2"
base_subfolder_name = "Analysis_"

# Segmentation parameters (DoG + Otsu)
SIGMA_A = 1.0  # smaller sigma for DoG (e.g. 2)
SIGMA_B = 4.0  # larger sigma for DoG (e.g. 7)
MIN_AREA = 50  # minimum accepted cell area (pixels)
MAX_AREA_PIXELS = 200  # maximum allowed cell area in pixels (set to None to disable)
StepN = 3  # save overlay every StepN frames (1 = save all)
frame_interval_s = 1  # seconds per frame (for plotting)

# ROI selection frame (0-based). By default use frame 0 to draw ROIs.
ROI_SELECTION_FRAME = 0
# -----------------------------------------------------------------------------


# --------- Otsu function (keeps original approach) --------------------------
def otsu_threshold(image):
    """Simple Otsu threshold on flattened image."""
    pixels = image.ravel()
    pixels = pixels[np.isfinite(pixels)]
    if pixels.size == 0:
        return 0.0
    hist, bin_edges = np.histogram(pixels, bins=256)
    hist = hist.astype(float)
    total = hist.sum()
    if total == 0:
        return 0.0
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    weight1 = np.cumsum(hist)
    weight2 = total - weight1
    epsilon = 1e-12
    mean1 = np.cumsum(hist * bin_centers) / (weight1 + epsilon)
    mean_total = np.sum(hist * bin_centers)
    mean2 = (mean_total - np.cumsum(hist * bin_centers)) / (weight2 + epsilon)
    var_between = weight1 * weight2 * (mean1 - mean2) ** 2
    idx = np.nanargmax(var_between)
    return bin_centers[idx]


# ---- segmentation: DoG -> Otsu -> close -> fill -> keep largest + area guard -------
def segment_cell_dog_otsu(
    roi, sigma_a=SIGMA_A, sigma_b=SIGMA_B, min_area=MIN_AREA, max_area_pixels=None
):
    """
    Segment a (dark) cell inside roi using: DoG (G_a - G_b) -> Otsu -> close & fill -> largest component.
    If max_area_pixels is provided and the candidate mask area > max_area_pixels, mask is rejected.
    Returns boolean mask (same shape as roi).
    """
    if roi.size == 0:
        return np.zeros_like(roi, dtype=bool)

    img = roi.astype(float)

    # compute blurred images
    G_a = ndimage.gaussian_filter(img, sigma=sigma_a)
    G_b = ndimage.gaussian_filter(img, sigma=sigma_b)
    diff = G_a - G_b  # DoG

    # Otsu threshold on diff
    thr = otsu_threshold(diff)

    # We expect the cell to be darker in DoG => mask = diff < thr
    mask = diff < thr

    # Close small gaps and fill donut holes
    mask = ndimage.binary_closing(mask, structure=np.ones((3, 3), bool))
    mask = ndimage.binary_fill_holes(mask)

    # Keep only largest connected component (assume single cell per ROI)
    labeled, n = ndimage.label(mask)
    if n == 0:
        return np.zeros_like(mask, dtype=bool)

    sizes = np.bincount(labeled.ravel())
    sizes[0] = 0
    largest_label = np.argmax(sizes)
    final_mask = labeled == largest_label

    # Enforce min area
    if final_mask.sum() < min_area:
        return np.zeros_like(mask, dtype=bool)

    # Enforce max area if specified
    if (max_area_pixels is not None) and (final_mask.sum() > max_area_pixels):
        # reject excessive mask (likely leak into background)
        return np.zeros_like(mask, dtype=bool)

    return final_mask


# ---------------- ROI selection function (interactive) -----------------------
def get_rois(image):
    """Interactively draw rectangular ROIs on provided image. Returns list of boxes."""
    img = image.astype(np.float32)
    p1, p99 = np.percentile(img, (1, 99))
    if p99 <= p1:
        p1, p99 = img.min(), img.max()

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(img, cmap="gray", vmin=p1, vmax=p99)
    plt.axis("off")
    plt.show(block=False)

    rois = []
    i = 0
    while True:
        plt.title(f"ROI {i+1}: click two opposite corners (press Enter when finished)")
        plt.draw()
        pts = plt.ginput(2, timeout=-1)
        if len(pts) < 2:
            print("Finished ROI selection.")
            break
        (x1, y1), (x2, y2) = pts
        x_min, x_max = sorted([int(round(x1)), int(round(x2))])
        y_min, y_max = sorted([int(round(y1)), int(round(y2))])
        rois.append((x_min, x_max, y_min, y_max))
        rect = patches.Rectangle(
            (x_min, y_min),
            x_max - x_min,
            y_max - y_min,
            linewidth=1.5,
            edgecolor="r",
            facecolor="none",
        )
        ax.add_patch(rect)
        plt.draw()
        i += 1

    plt.close(fig)
    return rois


# ---------------- main measurement loop (whole video) -----------------------
def measure_rois_in_nd2(path):
    """
    Process the whole ND2 video (phase channel only). Returns:
      - df: DataFrame of areas (frames x ROIs)
      - rois: list of ROI boxes
      - masks: nested list masks[t][i]
    """
    with ND2Reader(path) as images:
        phase_idx = 0

        # Use specified frame to let user draw ROIs
        first_frame = np.array(images.get_frame_2D(c=phase_idx, t=ROI_SELECTION_FRAME))
        rois = get_rois(first_frame)
        n_rois = len(rois)
        if n_rois == 0:
            print("No ROIs defined. Aborting.")
            return None, None, None

        # precompute ROI areas in pixels to set max area in pixels
        roi_pixel_areas = []
        for x_min, x_max, y_min, y_max in rois:
            roi_area = max(1, (y_max - y_min) * (x_max - x_min))
            roi_pixel_areas.append(roi_area)

        n_frames = images.sizes.get("t", len(images))
        areas = np.zeros((n_frames, n_rois), dtype=float)
        masks = [[None for _ in range(n_rois)] for _ in range(n_frames)]

        for t in range(n_frames):
            img_phase = np.array(images.get_frame_2D(c=phase_idx, t=t))
            for i, (x_min, x_max, y_min, y_max) in enumerate(rois):
                roi = img_phase[y_min:y_max, x_min:x_max]
                max_area_pixels = MAX_AREA_PIXELS
                mask = segment_cell_dog_otsu(
                    roi,
                    sigma_a=SIGMA_A,
                    sigma_b=SIGMA_B,
                    min_area=MIN_AREA,
                    max_area_pixels=max_area_pixels,
                )
                masks[t][i] = mask
                areas[t, i] = mask.sum()

    frame_idx = np.arange(n_frames)
    df = pd.DataFrame(
        {f"ROI_{j+1}": areas[:, j] for j in range(n_rois)}, index=frame_idx
    )
    df.index.name = "frame"
    return df, rois, masks


# --------- Save segmentation overlays (boundary on raw ROI) ------------------
def save_segmentation_overlays(
    nd2_path, rois, masks, output_root, phase_idx=0, step=StepN
):
    """
    Save overlay images (boundary contours) for QC.
    Saves one image every 'step' frames for each ROI into ROI_i folders under output_root.
    """
    with ND2Reader(nd2_path) as images:
        n_frames = len(masks)
        for t in range(0, n_frames, step):
            img_phase = np.array(images.get_frame_2D(c=phase_idx, t=t))
            for i, (x_min, x_max, y_min, y_max) in enumerate(rois):
                mask = masks[t][i]
                if mask is None:
                    continue
                roi_img = img_phase[y_min:y_max, x_min:x_max]
                roi_folder = os.path.join(output_root, f"ROI_{i+1}")
                os.makedirs(roi_folder, exist_ok=True)

                fig, ax = plt.subplots()
                ax.imshow(roi_img, cmap="gray")
                try:
                    ax.contour(
                        mask.astype(float), levels=[0.5], colors="r", linewidths=0.8
                    )
                except Exception:
                    ax.imshow(np.ma.masked_where(~mask, mask), cmap="Reds", alpha=0.35)
                ax.set_axis_off()
                ax.set_title(f"ROI {i+1}, frame {t}")
                fname = os.path.join(roi_folder, f"frame_{t:04d}.png")
                fig.savefig(fname, bbox_inches="tight", pad_inches=0)
                plt.close(fig)


# ----------------- Long CSV saver (adapted from your original file) ------------
def save_long_fluorescence(df, output_csv, value_col_name="value"):
    """
    Convert a wide DataFrame with columns ROI_1, ROI_2, ...
    and index = frame into a long format: track_id, frame, <value_col_name>
    and save as CSV (comma-separated, header in first row).
    This function was taken from your original script.
    """
    long_df = df.reset_index().melt(
        id_vars="frame", var_name="track_id", value_name=value_col_name
    )
    # Convert "ROI_1" -> 1 (integer track_id)
    long_df["track_id"] = (
        long_df["track_id"].str.replace("ROI_", "", regex=False).astype(int)
    )
    long_df = long_df[["track_id", "frame", value_col_name]]
    long_df.to_csv(output_csv, index=False)


# ---------------- main execution ---------------------------------------------
if __name__ == "__main__":
    nd2_path = os.path.join(folder_path, file_name)
    df, rois, masks = measure_rois_in_nd2(nd2_path)

    # Make the SAVE folder (Find the next available folder number)
    i = 1
    while os.path.exists(os.path.join(folder_path, f"{base_subfolder_name}{i}")):
        i += 1
    output_folder = os.path.join(folder_path, f"{base_subfolder_name}{i}")
    os.makedirs(output_folder, exist_ok=True)

    if df is not None:
        # Save wide CSV (areas)
        output_csv = os.path.join(output_folder, "csv1_Cell_Areas_DoG_Otsu.csv")
        df.to_csv(output_csv, index=True)
        print("Saved wide areas CSV to:", output_csv)

        # Save long CSV (areas) using your helper (track_id, frame, area)
        long_csv_path = os.path.join(output_folder, "csv_LONG_Cell_Areas_DoG_Otsu.csv")
        save_long_fluorescence(df, long_csv_path, value_col_name="area")
        print("Saved LONG areas CSV to:", long_csv_path)

        # Save segmentation overlays (boundaries on raw ROI) for QC
        save_segmentation_overlays(
            nd2_path, rois, masks, output_folder, phase_idx=0, step=StepN
        )
        print("Saved segmentation overlays under:", output_folder)

        # Plot areas vs time (one plot)
        plt.figure()
        for col in df.columns:
            plt.plot(df.index * frame_interval_s, df[col], label=col)
        plt.xlabel("Time (s)")
        plt.ylabel("Area (pixels)")
        plt.title("Cell Area vs Time (DoG+Otsu)")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="x-small")
        plt.tight_layout()
        plot_path = os.path.join(output_folder, "1_Cell_Areas_DoG_Otsu.png")
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        print("Saved area plot to:", plot_path)

    print("Done — results saved to:", output_folder)
