# Repository Map

This guide explains what each major folder contains and how it fits into the
paper story.

## Root Files

- `README.md`: the main navigation hub for the repository.
- `latexmkrc`: LaTeX build configuration used by the manuscript.
- `requirements.txt` and `environment.yml`: Python dependency lists for rerunning
  the maintained analyses.

## `manuscript/`

This folder contains the manuscript and supplement source files. Treat it as
read-only.

- `manuscript/manuscript.tex`: main manuscript LaTeX source.
- `manuscript/Supporting_Information.tex`: supplement LaTeX source.
- `manuscript/REFERENCES.bib`, `manuscript/biophys-new.cls`, and
  `manuscript/biophysj.bst`: manuscript build support files (bibliography and
  class definitions).
- `manuscript/figures/`: publication figure artifacts. Do not edit, rename,
  regenerate, or replace files in this folder during accessibility cleanup.
  Code-generated panels are written under `outputs/figure-panels/` instead.

## `data/`

This is the canonical source for the shared data. It starts after upstream video
and image processing.

- `data/time-series/bead/`: bead/tethered-cell motor speed traces. Each file is a
  compact Parquet table for one assay condition, with one column per cell trace.
- `data/time-series/bead/manifest.csv`: metadata table that explains each bead
  trace: assay, osmolyte, concentration, cell ID, rotation direction, and
  binning method.
- `data/time-series/tmrm/`: curated TMRM fluorescence traces. These support the
  membrane-potential confirmation experiment.
- `data/time-series/cell-area/`: curated cell-area traces. These show how cell
  size changes during the osmotic shock.
- `data/Osmolarity-readings/`: spreadsheet measurements of solution osmolarity.
- `data/Viscosity/`: viscosity support data organized by osmolyte. Contains two
  subdirectories:
  - `data/Viscosity/Sorb/`: sorbitol viscosity data. Each concentration
    subfolder (200mM–500mM) holds a
    `normalized-averages-from-sorb-motor-speeds.csv` file, and an
    `Viscosity-measurments-calculations.xlsx` spreadsheet summarises all
    concentrations.
  - `data/Viscosity/Sucro/`: sucrose viscosity data. Identical layout to the
    sorbitol folder with `normalized-averages-from-sucro-motor-speeds.csv` per
    concentration and a matching xlsx spreadsheet.

## `code/`

This folder contains scripts and notebooks that start from `data/time-series/`.
It does not contain the upstream raw-video processing workflow.

- `code/TMRM-anaylsis/`: scripts that normalize TMRM fluorescence traces and
  generate population summaries.
- `code/Cell-area-anaylsis/`: scripts that normalize cell-area traces and
  generate population summaries.
- `code/bead-assay/`: bead assay helper code and notebooks for motor speed,
  viscosity controls, shock fits, and sustained adaptation.

The folder names `TMRM-anaylsis` and `Cell-area-anaylsis` are retained to avoid
path churn in the repository.

## `outputs/`

This is now a committed results and reader-facing output folder. It contains:

- `outputs/figure-panels/`: regenerated code-generated figure panels with
  manuscript-oriented filenames (PDF).
- `outputs/key-results/`: small CSV summaries and plain-English captions for
  quick inspection without running code:
  - `bead_trace_inventory.csv`, `cell_area_population_summary.csv`,
    `tmrm_population_summary.csv`: per-experiment result tables.
  - `figure_to_data_map.csv`: mapping of manuscript figures to source data files.
  - `plain_english_captions.md`: human-readable figure captions.

The canonical data remain in `data/`; `outputs/` helps readers understand and
inspect the results without starting from code.

## `docs/`

This folder contains explanatory guides:

- `BIOLOGICAL_CONTEXT.md`: why the system and measurements matter.
- `HOW_TO_READ_DATA.md`: column definitions, units, and transformations.
- `GLOSSARY.md`: plain-English definitions of technical terms.
- `RERUN_GUIDE.md`: step-by-step instructions for running the analyses.
- `bead-subsampling-analysis.md`: technical note on bead trace binning.
- `history-rewrite-paths.txt`: historical cleanup note listing excluded raw or
  upstream artifacts.

## `tests/`

`tests/test_repository_integrity.py` checks that the cleaned repository remains
internally consistent: expected files exist, data schemas are valid, notebooks
are cleaned, and supported text files do not contain local absolute paths.
