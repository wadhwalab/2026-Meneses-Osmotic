# Data Guide

This repository starts from curated downstream time-series data. Raw videos,
raw image stacks, upstream segmentation outputs, bead centroid tables,
center-coordinate tables, MATLAB figure files, and other large intermediate
processing products are not included.

## `time-series/bead`

The bead assay data are stored as wide Parquet tables. Each file contains:

- `frame`: the original `300 Hz` frame reference at the `0.1 s` bin midpoint.
- `time_s`: the canonical time axis in seconds.
- one column per single-cell motor trace.

The bead data have already been reduced to `0.1 s` mean-binned time series. The
manifest at `time-series/bead/manifest.csv` records the file path, trace column,
assay, osmolyte, condition, cell id, rotation direction, source lineage,
`time_bin_s`, reduction method, and frame-reference rate.

See `../docs/bead-subsampling-analysis.md` for the binning validation.

## `time-series/tmrm`

The TMRM data are curated fluorescence time series exported after upstream image
segmentation and fluorescence extraction. Each Parquet file contains:

- `track_id`: cell/track identifier.
- `frame`: frame number in the downstream fluorescence time series.
- `fluorescence`: extracted TMRM fluorescence value.

The maintained scripts use a `5 s` frame interval, shock frame `35`, and a
10-frame pre-shock baseline window by default.

## `time-series/cell-area`

The cell-area data are curated area time series exported after upstream image
segmentation. Each Parquet file contains:

- `track_id`: cell/track identifier.
- `frame`: frame number in the downstream area time series.
- `area`: extracted cell area value.

The maintained scripts use a `5 s` frame interval, shock frame `35`, and a
10-frame pre-shock baseline window by default.

## `Osmolarity-readings` And `Viscosity`

These folders contain supporting spreadsheet and CSV data used by the notebook
analysis and manuscript calculations. They are downstream summary inputs, not
raw acquisition files.
