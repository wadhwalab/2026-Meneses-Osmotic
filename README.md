# Osmotic Stress Triggers Fast and Reversible PMF Collapse in *Escherichia coli*

**Meneses, Javi, Dudebout, Belser, Yang & Wadhwa (2026)**

This repository is the data and code supplement for a study of how *E. coli*
responds immediately after a sudden increase in external osmolarity. The central
finding is that hyperosmotic shock causes a fast, reversible drop in proton
motive force (PMF), the membrane-energy gradient that powers bacterial motility
and other essential processes. The bacterial flagellar motor reports this drop
as a rapid slowdown, and TMRM fluorescence provides an independent check that
the membrane potential falls during the same stress.

The repository is organized so that a reader can inspect curated data, open
pre-generated results, and rerun the maintained analysis scripts. It starts from
processed time-series data rather than raw videos or microscope image stacks.

## Where To Start

- [Biological context](docs/BIOLOGICAL_CONTEXT.md): the plain-language story of
  the organism, assays, controls, and main biological interpretation.
- [How to read the data](docs/HOW_TO_READ_DATA.md): what each column means,
  what units are used, and how raw measurements were normalized.
- [Repository map](docs/REPOSITORY_MAP.md): what each folder contains and why it
  exists.
- [Glossary](docs/GLOSSARY.md): definitions of PMF, TMRM, osmolyte, tau, DFF,
  viscosity correction, and other technical terms.
- [Rerun guide](docs/RERUN_GUIDE.md): step-by-step instructions for installing
  dependencies and regenerating maintained outputs.
- [Outputs guide](outputs/README.md): code-generated figure panels and summary
  tables generated from the curated data.


## Repository Roadmap

```text
.
├── code/                 # Python scripts and bead-analysis notebooks
├── data/                 # Curated time-series and supporting spreadsheet data
├── docs/                 # Plain-English guides and technical cleanup notes
├── manuscript/           # LaTeX source and publication figures
│   ├── figures/          
│   ├── manuscript.tex
│   └── Supporting_Information.tex
├── outputs/              # Code-generated outputs
│   ├── figure-panels/    # figure panels
│   └── key-results/      # Summary tables
└── tests/                # Repository integrity checks
```

Generated analysis intermediates (`outputs/bead/`, `outputs/cell-area/`,
`outputs/tmrm/`) are excluded from version control and must be reproduced
locally by running the maintained scripts.

The data workflow begins at `data/time-series/`. Upstream image/video
processing, bead-center detection, segmentation outputs, MATLAB figure files,
and large acquisition files are not included.

## Main Data Types

| Data type | Location | Biological meaning |
|---|---|---|
| Bead / tethered-cell motor speed | `data/time-series/bead/*.parquet` | Rotation of a bead attached to a flagellar motor, used as a fast readout of PMF. |
| Bead trace manifest | `data/time-series/bead/manifest.csv` | Metadata linking each single-cell trace to assay type, osmolyte, shock concentration, and rotation direction. |
| TMRM fluorescence | `data/time-series/tmrm/*.parquet` | Fluorescent membrane-potential readout used to confirm depolarization. |
| Cell area | `data/time-series/cell-area/*.parquet` | Cell-size change during osmotic shock, used as physical context for shrinkage and recovery. |
| Osmolarity and viscosity support data | `data/Osmolarity-readings/`, `data/Viscosity/` | Measurements/calculations used to compare motor slowdown with osmotic strength and fluid viscosity. |

Parquet is the canonical machine-readable format for curated time-series data.
It is compact and preserves numeric tables well, but it usually requires Python,
R, or another data tool to open. For quick inspection without programming, see
the summaries under `outputs/key-results/`.

## Setup For Rerunning Analyses

Using `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Using Conda or Mamba:

```bash
conda env create -f environment.yml
conda activate meneses-osmotic
```

## Maintained Scripts

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

Generated products are written under `outputs/`. The existing analysis folders
there are preserved:

- `outputs/tmrm/`
- `outputs/cell-area/`
- `outputs/bead/`
- `outputs/figure-panels/`
- `outputs/key-results/`

## Notebooks

The cleaned bead notebooks are retained for transparent analysis exploration:

- `code/bead-assay/sucrose_shock_analysis.ipynb`
- `code/bead-assay/bead_shock_curve_fits.ipynb`
- `code/bead-assay/adaptation_curve_fitting.ipynb`

Notebook sections that depended on local upstream files or removed raw
intermediates are marked as archived notes. The supported starting point remains
the committed time-series data.

## Validation

Run the repository integrity checks with the same Python environment used for
the analysis dependencies:

```bash
python -m pytest tests
```

The tests check time-series schemas, bead manifest consistency, bead binning
metadata, supported filenames, and the absence of hard-coded local absolute
paths in supported code, notebooks, and documentation.
