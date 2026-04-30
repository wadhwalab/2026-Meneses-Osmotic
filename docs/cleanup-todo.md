# Publication-Readiness Notes

This repository is now organized as a lightweight, time-series-first supplement.
The supported workflow begins with curated time-series data in
`data/time-series/`.

## Current Boundary

- Upstream image/video processing is outside this repository.
- Raw videos/images, segmentation outputs, bead centroid or center-coordinate
  tables, MATLAB artifacts, and other large intermediates are not included.
- Publication figures in `figures/` and manuscript `.tex` files are treated as
  release artifacts.

## Implemented Cleanup

- Bead Parquet files store `0.1 s` mean-binned time series.
- The bead manifest records `time_bin_s`, `reduction`, and
  `frame_reference_fps`.
- Descriptive script and notebook filenames replace the original numbered or
  ambiguous names.
- Maintained scripts write generated files to ignored `outputs/` directories.
- Dependency files and repository integrity tests document the expected runtime
  environment.

## Useful Checks Before Release

Run these from the repository root:

```bash
pytest
python "code/TMRM-anaylsis/analyze_tmrm_population_dff.py"
python "code/Cell-area-anaylsis/analyze_cell_area_population_dff.py"
python "code/bead-assay/plot_viscosity_control.py"
```

Generated outputs should appear only under `outputs/`.
