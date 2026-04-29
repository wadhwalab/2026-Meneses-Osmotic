# -*- coding: utf-8 -*-
"""
Created on Thu Jan 15 15:45:22 2026

@author: fjavi
"""

import pandas as pd
from pathlib import Path

# 1) Set your folder path here manually
folder_path = r"C:\Users\lemenese\ASU Dropbox\KE-TF Biodesign ME Wadhwa\Wadhwa Lab\Luis_M\Osmotic-shock-motor-response-project-2022-2025\Data\Cell-area\400\combined"
folder = Path(folder_path)

dfs = []
offset = 0  # this will keep track of the current maximum track_id

# 2) Read all CSVs and make track_id globally unique
for csv_file in sorted(folder.glob("*.csv")):
    df = pd.read_csv(csv_file, usecols=["track_id", "frame", "area"])

    # make sure track_id is numeric
    df["track_id"] = pd.to_numeric(df["track_id"], errors="raise")

    # shift IDs by current offset so they don't collide with previous files
    df["track_id"] = df["track_id"] + offset

    # update offset to the new max so the next file starts after this one
    offset = df["track_id"].max()

    dfs.append(df)

# Concatenate and save
big_df = pd.concat(dfs, ignore_index=True)
output_file = folder / "merged_fluorescence_020.csv"
big_df.to_csv(output_file, index=False)

print(f"Merged file saved to: {output_file}")
