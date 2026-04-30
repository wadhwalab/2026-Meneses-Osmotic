# Bead Time-Series Subsampling Analysis

This note evaluates whether the bead/tethered-cell time series can be reduced
from the current 300 Hz traces without changing the downstream scientific
outputs.

The numerical audit was run on the current Parquet data in
`data/time-series/bead`. Detailed CSV outputs are in
`outputs/bead/subsampling-evaluation/`.

## Implementation Status

Implemented on April 30, 2026.

The canonical bead files in `data/time-series/bead/*.parquet` are now stored as
`0.1 s` mean-binned wide tables. The `time_s` column stores the bin midpoint.
The `frame` column stores `round(time_s * 300)`, preserving the original 300 Hz
frame reference used by older notebook cells that compute `frame / 300`.

The bead manifest includes explicit reduction metadata:

- `time_bin_s = 0.1`
- `reduction = mean_bin`
- `frame_reference_fps = 300`

The bead notebooks were also updated to use
`bead_time_series.median_kernel_size(...)` rather than hard-coded 301-sample
median filters. This keeps the smoothing window at about `1 s` after binning.

## Downstream Requirements

The bead analysis notebooks do not use sub-frame or sub-0.1 s information for
the manuscript-level conclusions.

| Downstream analysis | Current time handling | Main measured quantities |
|---|---|---|
| `sucrose_shock_analysis.ipynb` | 301-point median filter at 300 Hz, then 0.1 s mean bins | Collapse tau, recovery tau, collapse amplitude, population mean traces |
| `bead_shock_curve_fits.ipynb` | Same 0.1 s binned shock workflow for sucrose/sorbitol/sodium/clockwise assays | Collapse tau, recovery tau, amplitude summaries |
| `adaptation_curve_fitting.ipynb` | 301-point median filter, baseline normalization, multi-second fit windows | Population decay tau, single-cell recovery tau, plateau |
| `plot_viscosity_control.py` | Illustrative legacy CSV plotting | No additional high-frequency quantitative endpoint |

Important fit and summary windows:

- Baseline normalization: mostly `time <= 180 s` or `time < 180 s`.
- Collapse fit: `175-240 s`.
- Collapse amplitude windows: roughly `155-175 s` and `215-235 s`.
- Recovery fit: roughly `250-360 s` for shock traces.
- Adaptation recovery fit: `250-600 s`.

The fastest fitted collapse time constants in the full-rate workflow are on the
order of seconds, not milliseconds. Across the shock traces, the full-rate
median collapse tau is about `4.14 s`; the 5th to 95th percentile range is
about `1.31-7.63 s`.

## Comparison Method

I compared the current full-rate workflow against two reduced representations:

- Mean-binned traces: average all samples inside each time bin, then apply a
  1 s-equivalent median filter before fitting.
- Downsampled traces: take one representative sample at each time step, then
  apply the same 1 s-equivalent median filter.

Tested time steps were `0.1`, `0.25`, `0.5`, `1.0`, and `2.0 s`. The reference
was the current full 300 Hz data processed with the notebook-style 1 s median
filter. For shock notebooks, the reference also includes the existing 0.1 s
binning step.

## Key Results

Actual size after replacing the 22 full-rate bead Parquet files with
mean-binned wide tables:

| Representation | Time step | Size |
|---|---:|---:|
| Previous full-rate Parquet | 0.0033 s | 82.93 MB |
| Current mean-binned Parquet | 0.1 s | 9.45 MB |
| Mean-binned Parquet | 0.25 s | 3.83 MB |
| Mean-binned Parquet | 0.5 s | 1.97 MB |
| Mean-binned Parquet | 1.0 s | 1.05 MB |

Median absolute errors for mean-binned traces, relative to the current
full-rate workflow:

| Quantity | 0.1 s | 0.25 s | 0.5 s | 1.0 s | 2.0 s |
|---|---:|---:|---:|---:|---:|
| Shock collapse tau error | 0.038 s | 0.071 s | 0.086 s | 0.087 s | 0.114 s |
| Shock amplitude error | 0.0017 | 0.0025 | 0.0036 | 0.0034 | 0.0043 |
| Adaptation recovery tau error | 0.31 s | 0.52 s | 0.56 s | 1.03 s | 1.16 s |
| Adaptation plateau error | 0.00056 | 0.00065 | 0.00097 | 0.00134 | 0.00134 |
| Adaptation population decay tau error | 0.037 s | 0.113 s | 0.137 s | 0.136 s | 0.475 s |

Population mean traces were also stable. For shock population curves, median
normalized RMS error was:

| Time step | Median normalized RMS error |
|---:|---:|
| 0.1 s | 0.0057 |
| 0.25 s | 0.0066 |
| 0.5 s | 0.0077 |
| 1.0 s | 0.0055 |
| 2.0 s | 0.0085 |

Downsampling was consistently worse than mean-binning. For example, at `1.0 s`
resolution the 95th percentile shock collapse tau error was about `3.36 s` for
downsampled traces, compared with about `0.38 s` for mean-binned traces.

After the actual 0.1 s conversion, I repeated the downstream-style fits against
a temporary full-rate backup. Median absolute differences were:

| Quantity | Median absolute difference | 95th percentile difference |
|---|---:|---:|
| Shock collapse tau | 0.037 s | 0.372 s |
| Shock recovery tau | 0.045 s | 0.647 s |
| Shock collapse amplitude | 0.0016 | 0.0143 |
| Adaptation recovery tau | 0.269 s | 19.55 s |
| Adaptation plateau | 0.00055 | 0.0093 |
| Adaptation population decay tau | 0.043 s | 0.091 s |

## Interpretation

The existing downstream workflow already discards most information above 10 Hz
for the main shock analyses, because traces are median-filtered over about 1 s
and then binned to 0.1 s. The adaptation analysis fits much longer windows and
is also insensitive to sub-second detail after the 1 s median filter.

Mean-binning is the right reduction method because it preserves local averages
and suppresses aliasing. Simple decimation should not be used as the canonical
storage format.

## Recommendation

Use `0.1 s` mean-binned bead time series as the lightweight canonical data in
the Git repository.

Reasons:

- It matches the resolution already used by the shock notebooks.
- It reduces bead Parquet storage from about `82.93 MB` to about `9.44 MB`.
- It keeps fitted collapse tau errors far below biological/sample variability.
- It preserves population means, amplitudes, and adaptation plateaus.
- It avoids having to explain or defend a more aggressive reduction.

For an even smaller repo, `0.25 s` mean-binning appears scientifically safe for
the current downstream outputs, but `0.1 s` is the conservative minimum implied
by the existing code.

Do not store both full-rate and reduced bead data in Git. If sub-second motor
fluctuations might be analyzed later, keep the full 300 Hz traces outside Git
as an archival data product or release asset, and keep the repository centered
on the 0.1 s binned data used by the manuscript workflow.
