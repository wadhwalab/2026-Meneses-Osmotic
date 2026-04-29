# Most of this script comes from Shabduli
# Used to get centroid + center of rotation from a bead assay / tethered cell assay video
# This script is written for the way I keep files organized on my computer, so feel free to change anything to do with file arrangement
# I use two folders, one for storing the videos and one for storing the results, the parameters file will be saved with the results
# the values you input here will be saved in params.csv, which will be used for the other modules
# I move my results to another folder to make sure nothing gets overwritten when I rerun the program
# outputs: trajectory scatterplot, frame properties, center coordinates


import argparse
import os
import cv2
import pims
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets as mwidgets
from skimage.filters import threshold_multiotsu
from skimage.color import rgb2gray
from skimage import measure
import pandas as pd
from circle_fit import taubinSVD
from circle_fit import hyperLSQ
from circle_fit import kmh
import shutil
import scipy

import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()
avi_path = filedialog.askopenfilename(
    title="Select AVI video file", filetypes=[("AVI files", "*.avi")]
)
directory = os.path.dirname(avi_path)
FPS = int(input("FPS="))
results = filedialog.askdirectory(title="Select results folder")

import os

# opening avi files
files = [os.path.basename(avi_path)]
avi_files = [file for file in files if file.lower().endswith(".avi")]
file_number = "0"

# starting detection for each video
for avi_file in avi_files:
    avi_name = avi_file[:-4]
    os.mkdir(results + os.path.sep + avi_name)
    path = os.path.join(directory, avi_file)
    print(f"Analyzing file: {path}")
    vidcap = cv2.VideoCapture(path)
    fdir = results + os.path.sep + avi_name + os.path.sep + "imgs"
    os.mkdir(fdir)
    count = 0
    while True:
        frames, image = vidcap.read()  # reads frames from the video
        if frames:  # check if more video is left to extract images/frames
            fname = fdir + os.path.sep + str(count) + ".tiff"
            # print(fname)
            cv2.imwrite(
                fname, image
            )  # saves the image/frame to the specified directory
            # print("Extracted " + fname)
            count += 1  # increasing counter by one
        else:
            break
    vidcap.release()  # Release space and windows
    cv2.destroyAllWindows()

    # Opening video
    fms = pims.open(fdir + os.path.sep + "*.tiff")
    img_properties = pd.DataFrame([])
    f = 0  # initiate counter

    # Thresholding
    test_img = fms[-1]  # Using the last image to set threshold
    test_gray = rgb2gray(test_img[:, :, :3])
    test_blur = cv2.GaussianBlur(
        test_gray, (7, 7), 0
    )  # smoothing the image using Guassian Blur with a 7x7 kernel size - reference: https://www.geeksforgeeks.org/python-opencv-smoothing-and-blurring/
    # Using Multi-Otsu to find a threshold value - reference: https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_multiotsu.html
    thresholds = threshold_multiotsu(
        test_blur, classes=5
    )  # classes specifies the no. of different threshold regions for dividing the smoothened grayscale image.
    regions = np.digitize(test_blur, bins=thresholds)
    rgn = 3
    tsh = thresholds[
        rgn - 1
    ]  # threshold value index for the corresponding region is region index - 1
    test_binary = test_blur > tsh
    print("Detecting objects...")

    for img in fms:
        gscale = rgb2gray(
            img[:, :, :3]
        )  # converting image to grayscale, [:,:,:3] - specifies to use only 3 channels
        gauss_blr = cv2.GaussianBlur(
            gscale, (7, 7), 0
        )  # smoothing the image using Guassian Blur with a 7x7 kernel size - reference: https://www.geeksforgeeks.org/python-opencv-smoothing-and-blurring/
        # Using the threshold value from user input to convert all the images to a binary
        binary = (
            gauss_blr > tsh
        )  # for a white background but dark object, use binary = gauss_blr < tsh
        label = measure.label(binary)  # labels the object in the frame
        properties = measure.regionprops(label)
        if len(properties) < 1:
            attr = []
            print("Error: No obj detected")
        elif len(properties) == 1:
            attr = []
            f = f + 1  # update counter
            for obj in properties:
                centroid = [obj.centroid]  # centroid of each particle
                cpy = centroid[0][
                    0
                ]  # x coordinate of the centroid -> https://scikit-image.org/docs/0.19.x/user_guide/numpy_images.html#coordinate-conventions
                cpx = centroid[0][1]  # y coordinate of the centroid
                alist = [
                    obj.area,
                    cpx,
                    cpy,
                    obj.major_axis_length,
                    obj.minor_axis_length,
                    f,
                ]  # list of calculated features of the particle
                attr.append(alist)
        else:
            attr = []
            print(f"Error: Multiple objs detected")
        img_props = pd.DataFrame(
            attr, columns=["area", "x", "y", "Majoraxis", "Minoraxis", "frame"]
        )  # specifying column names
        img_properties = pd.concat(
            [img_properties, img_props]
        )  # concatenates data of each frame
    img_properties.to_csv(
        results + os.path.sep + avi_name + os.path.sep + "frame-properties-df.csv"
    )  # exporting frame properties
    # dframe = pd.read_csv(results + os.path.sep + avi_name + os.path.sep + "frame-properties-df.csv")
    centroid_coords = img_properties[
        ["x", "y"]
    ].to_numpy()  # coordinates of the centroid of the cell in each frame
    x = img_properties["x"].to_numpy()
    y = img_properties["y"].to_numpy()

    #   Using centroids from OVERLAPPING windows to get the center of rotation
    print("Calculating center of rotation...")
    windowsize = FPS * 10  # window size is framerate x 10
    centre_X = []
    centre_Y = []
    for i in range(0, len(centroid_coords)):
        if i <= len(centroid_coords) - windowsize:
            j = int(i + windowsize)
            ctd_slice = centroid_coords[i:j]
            xc, yc, r, sigma = kmh(ctd_slice)
            centre_X.append(xc)
            centre_Y.append(yc)
        else:
            shift_to_left_by = int(i - (len(centroid_coords) - windowsize))
            shifted_i = i - shift_to_left_by
            ctd_slice = centroid_coords[shifted_i : len(centroid_coords)]
            xc, yc, r, sigma = kmh(ctd_slice)
            centre_X.append(xc)
            centre_Y.append(yc)
    cdata = {"x": centre_X, "y": centre_Y}
    cframe = pd.DataFrame(cdata)
    cframe.to_csv(
        results + os.path.sep + avi_name + os.path.sep + "center-coordinates.csv"
    )  # exporting center coordinates
    # Plotting trajectory
    centroid_X = centroid_coords[:, 0]
    centroid_Y = centroid_coords[:, 1]
    plt.scatter(centroid_X, centroid_Y)
    plt.savefig(
        results + os.path.sep + avi_name + os.path.sep + "trajectory-scatterplot.png",
        dpi=300,
    )
    plt.clf()

    # deleting images
    print(f"Finishing analysis of {path}")
    shutil.rmtree(fdir)

    # increment file number
    placeholder = int(file_number)
    placeholder = placeholder + 1
    file_number = str(placeholder)
# Saving inputs to params.csv in results folder
params = {"FPS": [FPS], "vp": [directory], "rp": [results], "Vnum": [file_number]}
df = pd.DataFrame(params)
pdir = results + os.path.sep + "params.csv"
df.to_csv(pdir, index=False)
