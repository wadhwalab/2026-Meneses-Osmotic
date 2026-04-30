# Bead Time-Series Subsampling Note

The committed bead/tethered-cell data in `data/time-series/bead` are compact `0.1 s` mean-binned versions of the original 300 Hz motor-speed traces. The
full-rate traces and upstream bead-center detection outputs are not included in this repository.

The bead manifest records the reduction explicitly with `time_bin_s = 0.1`,
`reduction = mean_bin`, and `frame_reference_fps = 300`. In the Parquet files, `time_s` is the canonical time column, while `frame` preserves the corresponding 300 Hz frame reference at each bin midpoint.

We compared the original full-rate traces with binned data and found that `0.1 s` mean-binning preserved the downstream shock, adaptation, and population-summary outputs used by the manuscript workflow. Relative to the full-rate analysis, median absolute differences after binning were small: about `0.037 s` for shock collapse tau, `0.045 s` for shock recovery tau, `0.0016` for shock collapse amplitude, `0.269 s` for adaptation recovery tau, `0.00055` for adaptation plateau, and `0.043 s` for adaptation population decay tau.

Because these errors are small relative to the downstream measurements, this repository provides only the binned bead data to reduce file size while preserving the downstream analysis.
