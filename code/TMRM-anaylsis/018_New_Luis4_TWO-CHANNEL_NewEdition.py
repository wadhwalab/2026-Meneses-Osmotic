# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 01:38:06 2026

@author: farha
Created on Thu Jan  8 14:00:36 2026

@author: fjavi
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches
from nd2reader import ND2Reader  # make sure nd2reader is installed
import pandas as pd
from scipy import ndimage

# ---Tweek parameters----------------------------------------------------------
SIGMA = (
    2.5  # Gaussian smoothing; ~1 (keept it between 1-3., and  check the test pictures)
)
min_area = (
    100  # Minimum area of a cell (smaller objects will be ignored in segmentation)
)
StepN = 2  # Save only 1 in every N images to test the segmentation. (if set as 1; gives all)
GrowMask = 4  # Grow mask for background to stay away from cell
frame_interval_s = 1  # (seconds) seconds per frame.

# Data Folder & File
folder_path = r"C:\Users\fjavi\ASU Dropbox\KE-TF Biodesign ME Wadhwa\Wadhwa Lab\Luis_M\Osmotic-shock-motor-response-project-2022-2025\Data\TMRM\Farhad\area-no-signal"
file_name = "cell-area-500mM-RO1-video001.nd2"

# Subfolder base for Saving Results, ROIs, etc.
base_subfolder_name = "Analysis_"


# --------FUNCTION: Otsu Threshold --------------------------------------------
def otsu_threshold(image):
    """
    Simple Otsu thresholding on a 2D image (NumPy array).
    Returns a scalar threshold.
    """
    # Flatten and drop NaNs
    pixels = image.ravel()
    pixels = pixels[np.isfinite(pixels)]

    if pixels.size == 0:
        return 0

    # 256-bin histogram over the actual intensity range
    hist, bin_edges = np.histogram(pixels, bins=256)
    hist = hist.astype(float)
    total = hist.sum()

    if total == 0:
        return 0

    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    # Cumulative sums
    weight1 = np.cumsum(hist)
    weight2 = total - weight1

    # Avoid division by zero
    epsilon = 1e-12
    mean1 = np.cumsum(hist * bin_centers) / (weight1 + epsilon)
    mean_total = np.sum(hist * bin_centers)
    mean2 = (mean_total - np.cumsum(hist * bin_centers)) / (weight2 + epsilon)

    # Between-class variance
    var_between = weight1 * weight2 * (mean1 - mean2) ** 2

    # Best threshold index
    idx = np.nanargmax(var_between)
    return bin_centers[idx]


# --------FUNCTION: Otsu Smooth & Size filter ---------------------------------
def segment_cell_otsu(roi, min_area, sigma=SIGMA):
    """
    Segment a dark cell in a lighter background inside one ROI.

    Steps:
      1) Gaussian smoothing
      2) Otsu threshold
      3) Remove objects smaller than min_area
      4) Keep the largest remaining object (one cell)
    """
    # 1) Smooth to reduce noise
    roi_float = roi.astype(float)
    smoothed = ndimage.gaussian_filter(roi_float, sigma=sigma)

    # 2) Otsu threshold on smoothed image
    thr = otsu_threshold(smoothed)
    raw_mask = smoothed < thr  # dark cell = True

    # 3) Remove tiny objects using connected components
    labeled, num = ndimage.label(raw_mask)
    if num == 0:
        return np.zeros_like(raw_mask, dtype=bool)

    sizes = np.bincount(labeled.ravel())
    sizes[0] = 0  # background label 0 → ignore

    # labels with area >= min_area
    keep = np.where(sizes >= min_area)[0]
    if keep.size == 0:
        # nothing big enough → return empty mask
        return np.zeros_like(raw_mask, dtype=bool)

    # 4) Keep only the largest object among those
    largest_label = keep[np.argmax(sizes[keep])]
    clean_mask = labeled == largest_label

    return clean_mask


# --------FUNCTION: Get ROI's -------------------------------------------
def get_rois(image):
    """Interactively let the user draw as many rectangular ROIs as they want.

    Finish by pressing Enter (or the stop mouse button) instead of clicking.
    Returns a list of (x_min, x_max, y_min, y_max) for each ROI.

    (X The image is contrast-stretched to 0..65535 for display only. Actually NO! HAHA!)
    Image contrast is enhanced using percentile clipping for display only.
    """
    img = image.astype(np.float32)

    # Percentile-based contrast stretch (ignore extreme outliers)
    p1, p99 = np.percentile(img, (1, 99))
    if p99 <= p1:  # degenerate case
        p1, p99 = img.min(), img.max()

    fig, ax = plt.subplots()
    # Use vmin/vmax to force high contrast
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


# ------FUNCTION: Measure Areas in ROI's-------------------------------------------
def measure_rois_in_nd2(path):
    """
    - Uses phase channel (c=0) for ROI selection and segmentation.
    - For each ROI and each time frame:
        * performs Otsu segmentation on the ROI (dark cell vs light background)
        * computes cell area in pixels
        * stores the binary mask for later use

    Returns
    -------
    df : pandas.DataFrame
        Row = frame number (over time).
        Columns = ROI_i (area in pixels).
    rois : list of tuples
        ROI boxes as (x_min, x_max, y_min, y_max).
    masks : list of lists of 2D arrays.
        masks[t][i] is a 2D boolean array for frame t, ROI i.
    """
    with ND2Reader(path) as images:
        phase_idx = 0  # <- known: phase channel = 0

        # First frame of phase channel for ROI selection
        first_frame_phase = np.array(images.get_frame_2D(c=phase_idx, t=0))

        # Let user draw as many ROIs as they want on the phase image
        rois = get_rois(first_frame_phase)
        n_rois = len(rois)

        if n_rois == 0:
            print("No ROIs defined, aborting.")
            return None, None, None

        # Number of time frames (t dimension)
        n_frames = images.sizes.get("t", len(images))

        # Area per frame per ROI
        areas = np.zeros((n_frames, n_rois), dtype=float)

        # Masks: list of length n_frames, each is a list of length n_rois
        masks = [[None for _ in range(n_rois)] for _ in range(n_frames)]

        # Loop over all time frames
        for t in range(n_frames):
            img_phase = np.array(images.get_frame_2D(c=phase_idx, t=t))

            for i, (x_min, x_max, y_min, y_max) in enumerate(rois):
                roi = img_phase[y_min:y_max, x_min:x_max]

                # Enhanced segmentation: Gaussian + Otsu + area filter
                mask = segment_cell_otsu(roi, min_area, SIGMA)

                # Store mask and area
                masks[t][i] = mask
                areas[t, i] = mask.sum()  # pixel count

    # Build results DataFrame
    frame_idx = np.arange(n_frames)
    data = {f"ROI_{i+1}": areas[:, i] for i in range(n_rois)}
    df = pd.DataFrame(data, index=frame_idx)
    df.index.name = "frame"

    return df, rois, masks


# --------FUNCTION: Fluorescence Intensity inside the Masks---------------------
def compute_fluorescence_intensity(nd2_path, rois, masks, fluor_idx=1):
    """
    Using existing masks (from the phase channel), compute the mean
    fluorescence intensity inside each cell mask, for each ROI and frame.

    Parameters
    ----------
    nd2_path : str
        Path to the ND2 file.
    rois : list of tuples
        (x_min, x_max, y_min, y_max) for each ROI.
    masks : list of lists of 2D boolean arrays
        masks[t][i] is the mask for frame t, ROI i.
    fluor_idx : int
        Channel index for fluorescence (1 in your case).

    Returns
    -------
    df_fl : pandas.DataFrame
        Index = frame number.
        Columns = ROI_i (mean fluorescence inside the cell).
    """
    with ND2Reader(nd2_path) as images:
        n_frames = len(masks)
        n_rois = len(rois)

        # Initialize with NaNs
        fluor_means = np.full((n_frames, n_rois), np.nan, dtype=float)

        for t in range(n_frames):
            # Fluorescence image at this frame
            img_fl = np.array(images.get_frame_2D(c=fluor_idx, t=t))

            for i, (x_min, x_max, y_min, y_max) in enumerate(rois):
                mask = masks[t][i]
                if mask is None:
                    continue

                # Crop fluorescence ROI
                roi_fl = img_fl[y_min:y_max, x_min:x_max]

                # Mean intensity inside the cell mask
                if mask.any():
                    fluor_means[t, i] = roi_fl[mask].mean()
                else:
                    fluor_means[t, i] = np.nan

    # Build DataFrame
    frame_idx = np.arange(n_frames)
    data_fl = {f"ROI_{i+1}": fluor_means[:, i] for i in range(n_rois)}
    df_fl = pd.DataFrame(data_fl, index=frame_idx)
    df_fl.index.name = "frame"

    return df_fl


# --------Save Segmentation Figures -------------------------------------------
def save_segmentation_figures(
    nd2_path, rois, masks, output_root, phase_idx=0, step=StepN
):
    """
    For each ROI, create a folder ROI_1, ROI_2, ... inside `output_root`
    and save one image every `step` frames with the segmented cell boundary
    overlaid on the phase-contrast ROI.
    """
    with ND2Reader(nd2_path) as images:
        n_frames = len(masks)

        # Loop over frames with a step: 0, 10, 20, ...
        for t in range(0, n_frames, step):
            img_phase = np.array(images.get_frame_2D(c=phase_idx, t=t))

            for i, (x_min, x_max, y_min, y_max) in enumerate(rois):
                mask = masks[t][i]
                if mask is None:
                    continue

                # Crop phase image to ROI
                roi_img = img_phase[y_min:y_max, x_min:x_max]

                # Make sure the folder for this ROI exists (under output_root)
                roi_folder = os.path.join(output_root, f"ROI_{i+1}")
                os.makedirs(roi_folder, exist_ok=True)

                # Plot with boundary overlay
                fig, ax = plt.subplots()
                ax.imshow(roi_img, cmap="gray")
                ax.contour(mask.astype(float), levels=[0.5])
                ax.set_axis_off()
                ax.set_title(f"ROI {i+1}, frame {t}")

                # Save
                fname = os.path.join(roi_folder, f"frame_{t:04d}.png")
                fig.savefig(fname, bbox_inches="tight", pad_inches=0)
                plt.close(fig)


# ------------FUNCTION: Background of Fluorescence Channel----------------------
def compute_fluorescence_background(
    nd2_path, rois, masks, fluor_idx=1, dilate_pixels=GrowMask
):
    """
    Using existing masks (from the phase channel), compute the mean
    fluorescence intensity of the *background* (outside a dilated cell mask)
    for each ROI and frame.

    Background = pixels in the ROI that are NOT in the dilated cell mask.

    Parameters
    ----------
    nd2_path : str
        Path to the ND2 file.
    rois : list of tuples
        (x_min, x_max, y_min, y_max) for each ROI.
    masks : list of lists of 2D boolean arrays
        masks[t][i] is the cell mask for frame t, ROI i (True = cell).
    fluor_idx : int
        Channel index for fluorescence (1 in your case).
    dilate_pixels : int
        How many pixels to grow the cell mask before inverting.
    """
    with ND2Reader(nd2_path) as images:
        n_frames = len(masks)
        n_rois = len(rois)

        bg_means = np.full((n_frames, n_rois), np.nan, dtype=float)

        for t in range(n_frames):
            img_fl = np.array(images.get_frame_2D(c=fluor_idx, t=t))

            for i, (x_min, x_max, y_min, y_max) in enumerate(rois):
                cell_mask = masks[t][i]
                if cell_mask is None:
                    continue

                # Crop fluorescence ROI
                roi_fl = img_fl[y_min:y_max, x_min:x_max]

                # Grow the cell mask to push background farther away
                grown_mask = ndimage.binary_dilation(
                    cell_mask, iterations=dilate_pixels
                )

                # Background = outside the grown mask
                bg_mask = ~grown_mask

                # If dilation killed all background pixels, fall back to simple inverse
                if not bg_mask.any():
                    bg_mask = ~cell_mask

                if bg_mask.any():
                    bg_means[t, i] = roi_fl[bg_mask].mean()
                else:
                    bg_means[t, i] = np.nan

    frame_idx = np.arange(n_frames)
    data_bg = {f"ROI_{i+1}": bg_means[:, i] for i in range(n_rois)}
    df_bg = pd.DataFrame(data_bg, index=frame_idx)
    df_bg.index.name = "frame"

    return df_bg


# ---------FUNCTION: Long CSV format (Gets Dataframe)--------------
def save_long_fluorescence(df, output_csv, value_col_name="fluorescence"):
    """
    Convert a wide DataFrame with columns ROI_1, ROI_2, ...
    and index = frame into a long format:

        track_id, frame, <value_col_name>

    and save as CSV (comma-separated, header in first row).
    """
    # df.index is 'frame', columns are 'ROI_1', 'ROI_2', ...
    long_df = df.reset_index().melt(  # bring 'frame' out of the index
        id_vars="frame", var_name="track_id", value_name=value_col_name
    )

    # Convert "ROI_1" -> 1 (integer track_id)
    long_df["track_id"] = (
        long_df["track_id"].str.replace("ROI_", "", regex=False).astype(int)
    )

    # Order columns as requested
    long_df = long_df[["track_id", "frame", value_col_name]]

    # Save CSV, comma is default, header in first row
    long_df.to_csv(output_csv, index=False)


# ------ CODE EXECUTION (or simply RUN)!!!! ------------------------------------
if __name__ == "__main__":
    nd2_path = os.path.join(folder_path, file_name)
    df, rois, masks = measure_rois_in_nd2(nd2_path)

    # Make the SAVE folder (Find the next available folder number)
    i = 1
    while os.path.exists(os.path.join(folder_path, f"{base_subfolder_name}{i}")):
        i += 1
    # Create the full path for the new SAVE folder
    output_folder = os.path.join(folder_path, f"{base_subfolder_name}{i}")
    # Actually create the directory on computer
    os.makedirs(output_folder)

    if df is not None:
        # CSV Files for 1. Areas, 2. Fluorescence, 3. Background of Fl --------

        output_csv = os.path.join(output_folder, "csv1_Cell_Areas_otsu.csv")
        df.to_csv(output_csv, index=True)

        # Mean fluorescence intensity inside each cell over time
        df_fl = compute_fluorescence_intensity(nd2_path, rois, masks, fluor_idx=1)
        df_fl.to_csv(os.path.join(output_folder, "csv2_Fluor_mean.csv"), index=True)

        df_bg = compute_fluorescence_background(nd2_path, rois, masks, fluor_idx=1)
        df_bg.to_csv(
            os.path.join(output_folder, "csv3_Backg_Fluor_mean.csv"), index=True
        )

        # Save segmentations as figures for quality control
        save_segmentation_figures(
            nd2_path, rois, masks, output_folder, phase_idx=0, step=StepN
        )

        # Subtract Normalization of Background for Fluorescent cells
        df_SubNormFl = df_fl - df_bg
        df_SubNormFl.to_csv(
            os.path.join(output_folder, "csv4_SubNorm_Fluor_mean.csv"), index=True
        )

        # Ratio Normalization of Background for Fluorescent cells
        df_RatNormFl = df_fl / df_bg
        df_RatNormFl.to_csv(
            os.path.join(output_folder, "csv5_RatioNorm_Fluor_mean.csv"), index=True
        )

        # save the Subtract-normalization as a long CSV:
        save_long_fluorescence(
            df_SubNormFl,
            os.path.join(output_folder, "csv444_LONG_SubtractNorm_Fluor_mean.csv"),
            value_col_name="fluorescence",
        )
        # save the Ratio-normalization as a long CSV:
        save_long_fluorescence(
            df_RatNormFl,
            os.path.join(output_folder, "csv555_LONG_RatioNorm_Fluor_mean_018_.csv"),
            value_col_name="fluorescence",
        )

        # Plot each ROI's area over time---------------------------------------
        plt.figure()
        for col in df.columns:
            # col is something like "ROI_1"
            label = col
            plt.plot(df.index * frame_interval_s, df[col], label=label)
        plt.xlabel("Time (s)")
        plt.ylabel("Area (pixels)")
        plt.title("Cell Area vs Time")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="x-small")
        plt.tight_layout()
        # SAVE FIGURE
        plot_path = os.path.join(output_folder, "1_Cell_Areas.png")
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()

        # Plot Fluorescence of each cell over time ----------------------------
        plt.figure()
        for col in df_fl.columns:
            label = col
            plt.plot(df_fl.index * frame_interval_s, df_fl[col], label=label)

        plt.xlabel("Time (s)")
        plt.ylabel(r"$I_{cell}$ (per Area)")
        plt.title("Cell Intensity (per Area) vs Time")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="x-small")
        plt.tight_layout()
        # SAVE FIGURE
        plot_path = os.path.join(output_folder, "2_Cell intensity.png")
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()

        # Plot Background of Fl vicinity of each cell over time ---------------
        plt.figure()
        for col in df_bg.columns:
            label = col
            plt.plot(df_bg.index * frame_interval_s, df_bg[col], label=label)

        plt.xlabel("Time (s)")
        plt.ylabel(r"$I_{Background}$ (per Area)")
        plt.title("Mean Background Intensity vs Time")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="x-small")
        plt.tight_layout()
        # SAVE FIGURE
        plot_path = os.path.join(output_folder, "3_Background instensity.png")
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()

        # Plot Subtract_Normal Fluorescence over time ---------------
        plt.figure()
        for col in df_SubNormFl.columns:
            label = col
            plt.plot(
                df_SubNormFl.index * frame_interval_s, df_SubNormFl[col], label=label
            )

        plt.xlabel("Time (s)")
        plt.ylabel(r"$I_{cell}$ - $I_{Background}$")
        plt.title("Cell Intensity subtracted by backround vs Time")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="x-small")
        plt.tight_layout()
        # SAVE FIGURE
        plot_path = os.path.join(output_folder, "4_Subtract.png")
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()

        # Plot Ratio_Normal Fluorescence over time ---------------
        plt.figure()
        for col in df_RatNormFl.columns:
            label = col
            plt.plot(
                df_RatNormFl.index * frame_interval_s, df_RatNormFl[col], label=label
            )

        plt.xlabel("Time (s)")
        plt.ylabel(r"$I_{cell}$ / $I_{Background}$")
        plt.title("Ratio of Cell to Background Intensity vs Time")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="x-small")
        plt.tight_layout()
        # SAVE FIGURE
        plot_path = os.path.join(output_folder, "5_Ratio.png")
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()

# FIN
