# Analysis Code Guide

The code in this directory starts from curated time-series data in
`data/time-series/`. Upstream image/video processing, segmentation, bead-center
detection, and raw acquisition data are outside the supported workflow for this
repository.

Generated files should go to `outputs/`, which is now committed as the
reader-facing results layer.

## TMRM Analysis

Folder: `code/TMRM-anaylsis/`

- `analyze_tmrm_population_dff.py` reads all curated TMRM Parquet files,
  computes per-track DeltaF/F0 values, writes per-condition CSVs, and saves a
  population panel under `outputs/figure-panels/`.
- `analyze_tmrm_single_condition_dff.py` runs the same normalization and basic
  CSV export for one condition file. Diagnostic plots are optional and are only
  written when `--figure-dir` is supplied.

Inputs: `data/time-series/tmrm/*.parquet` with `track_id`, `frame`, and
`fluorescence`.

## Cell-Area Analysis

Folder: `code/Cell-area-anaylsis/`

- `analyze_cell_area_population_dff.py` reads all curated cell-area Parquet
  files, computes per-track DeltaA/A0 values, writes per-condition CSVs, and
  saves a population panel under `outputs/figure-panels/`.
- `analyze_cell_area_single_condition_dff.py` runs the same normalization and
  CSV export for one condition file. Diagnostic plots are optional and are only
  written when `--figure-dir` is supplied.

Inputs: `data/time-series/cell-area/*.parquet` with `track_id`, `frame`, and
`area`.

## Bead Assay

Folder: `code/bead-assay/`

- `bead_time_series.py` is the maintained helper for reading the compact bead
  Parquet files and materializing legacy speed CSV trees under
  `outputs/bead/legacy-speed-tree/` when notebook code needs them.
- `plot_viscosity_control.py` is a maintained script that plots measured
  motor-speed traces against an expected viscosity-only speed drop.
- `sucrose_shock_analysis.ipynb`, `bead_shock_curve_fits.ipynb`, and
  `adaptation_curve_fitting.ipynb` are cleaned notebooks for transparent
  exploratory analysis from the curated time-series inputs.

Inputs: `data/time-series/bead/*.parquet` and
`data/time-series/bead/manifest.csv`.

Bead traces have already been reduced to `0.1 s` mean-binned time series. Use
`time_s` as the canonical time axis; `frame` preserves the original `300 Hz`
frame reference for compatibility with older analysis cells.
