# Osmotic Stress Triggers Fast and Reversible PMF Collapse in *Escherichia coli*

**Meneses, Javi, Dudebout, Belser, Yang & Wadhwa (2026)**

This repository contains the curated time-series data, downstream analysis code,
publication figures, and manuscript source for the osmotic-shock PMF study.

The repository now starts after raw video/image processing. Raw `.avi` and
`.nd2` files, segmentation overlays, bead centroid/center-coordinate tables,
MATLAB figure artifacts, and other upstream intermediates are intentionally not
part of the working tree.

## Repository Structure

```text
.
├── code/
│   ├── TMRM-anaylsis/           # restored downstream TMRM post-analysis scripts
│   ├── Cell-area-anaylsis/      # restored downstream area post-analysis scripts
│   └── bead-assay/              # bead plotting/fitting notebooks and helpers
├── data/
│   ├── time-series/
│   │   ├── bead/                # bead/tethered-cell motor frequency traces
│   │   ├── tmrm/                # merged TMRM fluorescence traces
│   │   └── cell-area/           # merged cell-area traces
│   ├── Osmolarity-readings/
│   └── Viscosity/
├── figures/                     # publication-ready figures
├── manuscript.tex
├── Supporting_Information.tex
└── REFERENCES.bib
```

Generated analysis products are written to `outputs/`, which is ignored by Git.

## Canonical Data Inputs

The downstream analysis starts from these Parquet schemas:

| Pipeline | Location | Required columns |
|---|---|---|
| Bead / tethered-cell motor speed | `data/time-series/bead/*.parquet` | `frame`, `time_s`, plus one column per trace |
| Bead trace manifest | `data/time-series/bead/manifest.csv` | `path`, `column_name`, `assay`, `osmolyte`, `condition_mM`, `cell_id`, `rotation_direction`, `fps`, `source_kind`, `source_path`, `sign_adjustment`, `time_bin_s`, `reduction`, `frame_reference_fps` |
| TMRM fluorescence | `data/time-series/tmrm/*.parquet` | `track_id`, `frame`, `fluorescence` |
| Cell area | `data/time-series/cell-area/*.parquet` | `track_id`, `frame`, `area` |

Each bead file is a compressed wide table for one assay/condition. Bead traces
are stored as `0.1 s` mean-binned time series, which matches the resolution used
by the downstream shock-analysis notebooks. The `time_s` column is the
authoritative time axis. The `frame` column stores the original `300 Hz` frame
reference at each bin midpoint so older notebook cells that compute
`frame / 300` still recover time in seconds.

The small CSV manifest maps each trace to its `column_name` inside that file
and includes the legacy source path used during curation, so the data lineage
remains visible even though upstream folders are removed from the working tree.
See `docs/bead-subsampling-analysis.md` for the binning validation and
post-conversion fidelity checks.

## Running Analysis

Use Python 3 with the scientific Python stack used by the original analysis
scripts (`numpy`, `pandas`, `matplotlib`, and `pyarrow` for Parquet).
Some bead notebooks also use `scipy`, `seaborn`, and `scikit-learn`.

```bash
python "code/TMRM-anaylsis/021_MergeMultiDFF.py"
python "code/Cell-area-anaylsis/021-2 MergeMultiDFF_AREA__.py"
```

Outputs:

- `outputs/tmrm/dff/` and `outputs/cell-area/dff/`: regenerated per-condition
  normalized traces.
- `outputs/tmrm/` and `outputs/cell-area/`: combined population plots from the
  restored downstream scripts.

The restored bead notebooks remain under `code/bead-assay/` and start from
motor-frequency time-series, not raw bead-center detection. They use
`code/bead-assay/bead_time_series.py` to read the compact wide Parquet files in
`data/time-series/bead/`. When an older notebook cell still expects a legacy
`speeds/<condition>/*.csv` tree, the helper materializes that tree under
`outputs/bead/legacy-speed-tree/` from the canonical Parquet inputs.
The helper also provides a time-aware median-filter kernel so a 1 s smoothing
window remains 1 s after the bead data reduction.

## Analysis Parameters

| Parameter | Value |
|---|---|
| TMRM/cell-area shock frame | `35` |
| TMRM/cell-area baseline window | `10` frames before shock |
| TMRM/cell-area frame interval | `5 s` |
| Bead baseline interval | `time < 180 s` |
| Default bead frame rate | `300 fps` |

## Manuscript

The manuscript is written in LaTeX. To compile:

```bash
latexmk -pdf manuscript.tex
```

## Git History Note

Deleting large upstream files in a normal commit reduces the checked-out working
tree, but it does not shrink the existing `.git` object database or future clone
history. A separate history rewrite is required for that. The path patterns to
purge later are listed in `docs/history-rewrite-paths.txt`.
