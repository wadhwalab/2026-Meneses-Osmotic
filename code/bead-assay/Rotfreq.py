# PLEASE PLEASE PLEASE READ: IF YOU ARE ANALYZING CW ROTATION MULTIPLY LINE 72 BY -1. DO NOT MULTIPLY IF YOU ARE ANALYZING CCW ROTATION.
# corrects center coordinates, calculates frequency, filters frequency, plots frequency
# you will need to enter the params.csv file you got from Detection.py
# this file contains the information on FPS + where your results files are located
# outputs: frequency csv, updated center coordinates, frequency plot
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import scipy


# Rotation speed
def get_rotfreq(x, y, xcen, ycen, frate):
    xcomp = x - xcen  # x component of the vector from center of rotation to centroid
    ycomp = y - ycen  # y component of the vector from center of rotation to centroid
    theta = np.unwrap(np.arctan2(ycomp, xcomp))  # UNWRAP function
    f = frate * np.diff(theta) / (2 * np.pi)
    return f


# Displacement between two points:
def disp(x1, y1, x0, y0):
    return np.sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0))


# fill out params
pdir = input("Input parameters csv (please):")
pf = pd.read_csv(pdir)
names = pf.to_numpy()
FPS = names[0][0]
rdir = names[0][2]

# cycling through folders
all_items = os.listdir(rdir)
folders = [item for item in all_items if os.path.isdir(os.path.join(rdir, item))]
for folder in folders:
    # taking useful data from files
    fdir = os.path.join(rdir, folder)
    properties = pd.read_csv(fdir + os.path.sep + "frame-properties-df.csv")
    center = pd.read_csv(fdir + os.path.sep + "center-coordinates.csv")
    x = properties["x"].to_numpy()
    y = properties["y"].to_numpy()
    mjr_ax = properties["Majoraxis"].to_numpy()
    xc = center["x"].to_numpy()
    yc = center["y"].to_numpy()

    # correcting center coordinates - if distance traveled over 10 frames is less than the diameter of the cell (major axis) then correct center coordinates
    i_list = np.arange(1, len(x), dtype="int")
    dia = np.mean(mjr_ax)
    thresh = (
        0.5  # for tethered cell assays set this to 1, for bead assays set this to 0.5?
    )
    displacements = np.zeros(len(x))
    for i in i_list:
        d = disp(x[i], y[i], x[i - 1], y[i - 1])
        displacements[i] = d
    sums = []
    for i in i_list:
        sum = np.sum(displacements[i : i + 10])
        sums.append(sum)
    corrected_sum = sums / dia
    j_list = np.arange(1, len(x) - 1, dtype="int")
    for j in j_list:
        if corrected_sum[j] <= thresh:
            xc[j] = xc[j - 1]
            yc[j] = yc[j - 1]
        else:
            continue

    # calculate frequency
    freq = get_rotfreq(x, y, xc, yc, FPS)
    # filtering frequency with a median filter
    freq_filt = scipy.signal.medfilt(freq, kernel_size=51)

    # PLOTTING FILTERED FREQUENCY HERE: CHANGE PLOT SETTINGS HERE
    seconds = np.arange(0, len(x) - 1) / FPS
    figure = plt.figure(figsize=(10, 5.5))
    ax1 = figure.add_subplot(111)
    ax1.plot(seconds, freq_filt, c="grey")
    plt.tick_params(which="both", direction="in")
    # plt.xticks(np.arange(min(seconds), max(seconds), 120), fontsize=20)
    plt.yticks(fontsize=20)
    plt.xticks(np.arange(0, 1200, 200), fontsize=20)
    # plt.yticks(np.arange(0, 81, 10), fontsize=20)
    plt.xlim(0, 1200)
    plt.ylim(0, 80)
    ax1.set_xlabel("Time (s)", fontsize=20)
    ax1.set_ylabel("Frequency (Hz)", fontsize=20)
    # plt.legend(loc="lower right", fontsize=20)
    # Highlight a region with shading
    plt.axvspan(180, 1200, color="lightgrey", alpha=1)
    # Add darker dashed vertical lines
    # plt.title("300mM-cell1-microfluidic", fontsize=20)
    plt.savefig(fdir + os.path.sep + "freq-plot.pdf", dpi=300)
    plt.show()

    # saving the FILTERED frequency
    ff = pd.DataFrame(freq_filt)
    ff.to_csv(fdir + os.path.sep + "freq.csv")

    # saving the UPDATED center coordinates
    cdata = {"x": xc, "y": yc}
    cframe = pd.DataFrame(cdata)
    cframe.to_csv(
        fdir + os.path.sep + "new-center-coordinates.csv"
    )  # exporting center coordinates
    print(corrected_sum)
    print(thresh)
