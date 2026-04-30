# Osmotic Stress Triggers Fast and Reversible PMF Collapse in *Escherichia coli*

**Meneses, Javi, Dudebout, Belser, Yang & Wadhwa (2026)**

This repository is the data and code supplement for the osmotic-shock PMF
study. It is organized as a lightweight, time-series-first workflow: readers can
inspect the curated data, rerun the downstream analysis scripts, and compare
generated outputs with the publication figures.

The manuscript text and files under `figures/` are release artifacts and are not
part of the cleanup workflow. Generated analysis products are written to
`outputs/`, which is ignored by Git.

## Data Boundary

This repository intentionally starts after upstream image and video processing.
It does not include raw videos/images, upstream acquisition files, segmentation
outputs, bead centroid or center-coordinate tables, intermediate rotation
frequency files, MATLAB figure artifacts, or other large processing
intermediates.

The supported analysis workflow starts from the curated time-series data in
`data/time-series/`.

## Repository Structure

```text
.
├── code/
│   ├── TMRM-anaylsis/           # downstream TMRM analysis scripts
│   ├── Cell-area-anaylsis/      # downstream cell-area analysis scripts
│   └── bead-assay/              # bead assay notebooks, plotting scripts, helpers
├── data/
│   ├── time-series/
│   │   ├── bead/                # bead/tethered-cell motor frequency traces
│   │   ├── tmrm/                # curated TMRM fluorescence traces
│   │   └── cell-area/           # curated cell-area traces
│   ├── Osmolarity-readings/
│   └── Viscosity/
├── docs/                        # cleanup and data-reduction notes
├── figures/                     # publication figure artifacts
├── manuscript.tex
├── Supporting_Information.tex
└── REFERENCES.bib
```

The folder names `TMRM-anaylsis` and `Cell-area-anaylsis` are retained to avoid
unnecessary path churn, but the scripts inside them now use descriptive names.

## Setup

Using `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Using Conda or Mamba:

```bash
conda env create -f environment.yml
conda activate meneses-osmotic
```

## Canonical Inputs

| Pipeline | Location | Required columns |
|---|---|---|
| Bead / tethered-cell motor speed | `data/time-series/bead/*.parquet` | `frame`, `time_s`, plus one column per trace |
| Bead trace manifest | `data/time-series/bead/manifest.csv` | `path`, `column_name`, `assay`, `osmolyte`, `condition_mM`, `cell_id`, `rotation_direction`, `fps`, `source_kind`, `source_path`, `sign_adjustment`, `time_bin_s`, `reduction`, `frame_reference_fps` |
| TMRM fluorescence | `data/time-series/tmrm/*.parquet` | `track_id`, `frame`, `fluorescence` |
| Cell area | `data/time-series/cell-area/*.parquet` | `track_id`, `frame`, `area` |

Bead traces are stored as `0.1 s` mean-binned time series. The `time_s` column
is the canonical time axis. The `frame` column preserves the original `300 Hz`
frame reference at each bin midpoint, so older analysis cells that compute
`frame / 300` still recover time in seconds.

See `docs/bead-subsampling-analysis.md` for the binning validation and fidelity
checks.

## Running The Maintained Scripts

Run the population analyses:

```bash
python "code/TMRM-anaylsis/analyze_tmrm_population_dff.py"
python "code/Cell-area-anaylsis/analyze_cell_area_population_dff.py"
```

Run a single-condition example:

```bash
python "code/TMRM-anaylsis/analyze_tmrm_single_condition_dff.py" --input-file data/time-series/tmrm/200mM.parquet
python "code/Cell-area-anaylsis/analyze_cell_area_single_condition_dff.py" --input-file data/time-series/cell-area/200mM.parquet
```

Run the bead viscosity-control plotting example:

```bash
python "code/bead-assay/plot_viscosity_control.py"
```

Outputs are written under:

- `outputs/tmrm/`
- `outputs/cell-area/`
- `outputs/bead/`

The bead notebooks use `code/bead-assay/bead_time_series.py` to read the compact
wide Parquet files. When older notebook logic expects a legacy
`speeds/<condition>/*.csv` tree, the helper materializes that tree under
`outputs/bead/legacy-speed-tree/` from the canonical Parquet inputs.

## Notebooks

The cleaned bead notebooks are retained for transparent analysis exploration:

- `code/bead-assay/sucrose_shock_analysis.ipynb`
- `code/bead-assay/bead_shock_curve_fits.ipynb`
- `code/bead-assay/adaptation_curve_fitting.ipynb`

Notebook sections that depended on local upstream files or removed raw
intermediates are marked as archived notes. The supported starting point remains
the committed time-series data.

## Validation

Run the repository integrity checks with:

```bash
pytest
```

The tests check time-series schemas, bead manifest consistency, bead binning
metadata, renamed supported filenames, and the absence of hard-coded local
absolute paths in supported code and notebooks.
