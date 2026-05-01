# Repository Map

This guide explains what each major folder contains and how it fits into the
paper story.

## Root Files

- `README.md`: the main navigation hub for the repository.
- `manuscript.tex`, `main.tex`, and `Supporting_Information.tex`: manuscript and
  supplement sources used as references for figure mapping. These files should
  remain untouched.
- `REFERENCES.bib`, `biophys-new.cls`, `biophysj.bst`, and `latexmkrc`:
  manuscript build support files.
- `requirements.txt` and `environment.yml`: Python dependency lists for rerunning
  the maintained analyses.

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
- `data/Viscosity/`: spreadsheet and CSV support data used to estimate how much
  motor speed should change from fluid viscosity alone.

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

## `figures/`

This folder contains publication figure artifacts. Treat it as read-only. Do not
edit, rename, regenerate, or replace files in this folder during accessibility
cleanup. Code-generated panels that resemble manuscript panels are written under
`outputs/figure-panels/` instead.

## `outputs/`

This is now a committed results and reader-facing output folder. It contains:

- regenerated analysis products from maintained scripts,
- code-generated figure panels with manuscript-oriented filenames,
- small CSV summaries for quick inspection,
- plain-English captions and mapping tables.

The canonical data remain in `data/`; `outputs/` helps readers understand and
inspect the results without starting from code.

## `docs/`

This folder contains explanatory guides:

- `BIOLOGICAL_CONTEXT.md`: why the system and measurements matter.
- `HOW_TO_READ_DATA.md`: column definitions, units, and transformations.
- `FIGURES_AT_A_GLANCE.md`: figure-to-data and figure-to-code map.
- `GLOSSARY.md`: plain-English definitions of technical terms.
- `RERUN_GUIDE.md`: step-by-step instructions for running the analyses.
- `bead-subsampling-analysis.md`: technical note on bead trace binning.
- `history-rewrite-paths.txt`: historical cleanup note listing excluded raw or
  upstream artifacts.

## `tests/`

`tests/test_repository_integrity.py` checks that the cleaned repository remains
internally consistent: expected files exist, data schemas are valid, notebooks
are cleaned, and supported text files do not contain local absolute paths.
