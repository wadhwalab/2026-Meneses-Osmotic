# Outputs Guide

`outputs/` is the committed, reader-facing results layer. It contains
code-generated figure panels, compact summaries, and processed tables that help
readers understand the paper without starting from raw code.

The canonical data remain in `data/`. Files in `outputs/` are derived from those
data. Figure files in this folder are code-generated panels, not copied
or rendered versions of the polished manuscript figures.

## Folders

- `outputs/figure-panels/`: code-generated figure panel PDFs with names that
  point back to the related manuscript panel, such as `figure-4a-...`.
- `outputs/tmrm/`: generated per-condition normalized fluorescence CSVs.
- `outputs/cell-area/`: generated per-condition normalized area CSVs.
- `outputs/bead/`: generated bead-analysis support outputs, including the
  viscosity-control example and temporary legacy-style speed trees used by
  notebooks.
- `outputs/key-results/`: small CSV summaries and plain-English captions that
  connect output files back to the paper story.

## How To Use This Folder

Open `outputs/key-results/figure_to_data_map.csv` for a compact table linking
figures, source data, code, and biological takeaways.

Open `outputs/figure-panels/` for the reproducible code-generated figure panels.
These are intentionally less polished than the Illustrator-finished manuscript
figures, but they show the same broad biological patterns.

Open `outputs/key-results/bead_trace_inventory.csv` to see how many bead motor
traces are available for each assay, osmolyte, concentration, and rotation
direction.

Open `outputs/key-results/tmrm_population_summary.csv` and
`outputs/key-results/cell_area_population_summary.csv` for quick population
summaries without loading Parquet files.
