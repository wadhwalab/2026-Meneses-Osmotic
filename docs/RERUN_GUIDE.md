# Rerun Guide

This guide explains how to regenerate the maintained outputs from the curated
data. It does not recreate upstream raw-video or image-segmentation steps.

## 1. Install Python Dependencies

Use one consistent Python environment for both analysis and tests.

On macOS or Linux:

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

With Conda or Mamba:

```bash
conda env create -f environment.yml
conda activate meneses-osmotic
```

## 2. Regenerate TMRM Outputs

```bash
python "code/TMRM-anaylsis/analyze_tmrm_population_dff.py"
```

Expected outputs:

- `outputs/figure-panels/figure-2b-tmrm-population.pdf`
- `outputs/tmrm/dff/*_dff.csv`

These files show baseline-normalized TMRM fluorescence changes for control and
200-500 mM sucrose shocks.

## 3. Regenerate Cell-Area Outputs

```bash
python "code/Cell-area-anaylsis/analyze_cell_area_population_dff.py"
```

Expected outputs:

- `outputs/figure-panels/supplement-cell-area-population.pdf`
- `outputs/cell-area/dff/*_dff.csv`

These files show baseline-normalized cell-area changes during osmotic shock.

## 4. Regenerate A Bead Viscosity-Control Output

```bash
python "code/bead-assay/plot_viscosity_control.py"
```

Expected outputs:

- `outputs/figure-panels/supplement-clockwise-viscosity-control.pdf`
- `outputs/bead/viscosity-cw/time_to_reach_y_range.txt`

This plot compares measured clockwise motor speed with a simple viscosity-only
prediction.

## 5. Regenerate Bead Motor-Speed Figure Panels

Open the bead notebooks in Jupyter or VS Code and run all supported cells:

- `code/bead-assay/sucrose_shock_analysis.ipynb`
- `code/bead-assay/bead_shock_curve_fits.ipynb`
- `code/bead-assay/adaptation_curve_fitting.ipynb`

Expected outputs:

- `outputs/figure-panels/figure-1d-sucrose-motor-speed.pdf`
- `outputs/figure-panels/figure-3a-sorbitol-motor-speed.pdf`
- `outputs/figure-panels/figure-4a-sodium-buffer-motor-speed.pdf`
- `outputs/figure-panels/figure-5a-clockwise-motor-speed.pdf`
- `outputs/figure-panels/figure-6a-adaptation-motor-speed.pdf`

These panels are generated directly from curated bead time-series data. They are
not copied or rendered from the polished manuscript figures.

## 6. Use The Bead Notebooks

Open these notebooks in Jupyter or VS Code:

- `code/bead-assay/sucrose_shock_analysis.ipynb`
- `code/bead-assay/bead_shock_curve_fits.ipynb`
- `code/bead-assay/adaptation_curve_fitting.ipynb`

The notebooks use curated bead time-series data and the helper
`code/bead-assay/bead_time_series.py`. Some archived cells describe older
upstream workflows that depended on raw or intermediate files no longer included
in the repository.

## 7. Run Integrity Checks

```bash
python -m pytest tests
```

If Parquet-related tests fail with a missing-engine message, install
dependencies into the active environment:

```bash
python -m pip install -r requirements.txt
```

The important point is that `python`, `pip`, and `pytest` should come from the
same environment.

## 8. What Not To Regenerate Here

This repository does not include:

- raw microscopy videos,
- raw image stacks,
- upstream segmentation outputs,
- bead centroid or center-coordinate tables,
- MATLAB figure artifacts,
- large local processing intermediates.

The supported workflow begins at `data/time-series/`.
