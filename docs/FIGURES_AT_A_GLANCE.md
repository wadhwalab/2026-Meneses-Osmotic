# Figures At A Glance

The manuscript files and `figures/` folder are references only and should remain
untouched. Code-generated panels are written under `outputs/figure-panels/`.

## Main Figures

| Figure | Source artifact | Code-generated panel | Data | Analysis path | Plain-English takeaway |
|---|---|---|---|---|---|
| Main Figure 1: sucrose motor response | `figures/sucrose.pdf` | `outputs/figure-panels/figure-1d-sucrose-motor-speed.pdf` | `data/time-series/bead/sucrose_*.parquet`, `data/Osmolarity-readings/sucrose.xlsx`, `data/Viscosity/Sucro/` | `code/bead-assay/sucrose_shock_analysis.ipynb`, `code/bead-assay/bead_shock_curve_fits.ipynb` | Sucrose shock rapidly slows the flagellar motor, and larger shocks cause larger slowdowns. |
| Main Figure 2: TMRM confirmation | `figures/quantification_TMRM.pdf` | `outputs/figure-panels/figure-2b-tmrm-population.pdf` | `data/time-series/tmrm/*.parquet` | `code/TMRM-anaylsis/` | TMRM fluorescence drops after shock, independently supporting a membrane-potential decrease. |
| Main Figure 3: sorbitol control | `figures/sorbitol-biophysics.pdf` | `outputs/figure-panels/figure-3a-sorbitol-motor-speed.pdf` | `data/time-series/bead/sorbitol_*.parquet`, `data/Osmolarity-readings/sorbitol.xlsx`, `data/Viscosity/Sorb/` | `code/bead-assay/bead_shock_curve_fits.ipynb` | A different non-ionic osmolyte causes a similar motor slowdown, so the effect is not sucrose-specific. |
| Main Figure 4: sodium phosphate buffer | `figures/sodium-biophysics.pdf` | `outputs/figure-panels/figure-4a-sodium-buffer-motor-speed.pdf` | `data/time-series/bead/sodium_*.parquet`, `data/Osmolarity-readings/sodium.xlsx` | `code/bead-assay/bead_shock_curve_fits.ipynb` | The rapid response persists without potassium in the buffer, so immediate potassium uptake is not required. |
| Main Figure 5: clockwise motors | `figures/clockwise-biophyscis.pdf` | `outputs/figure-panels/figure-5a-clockwise-motor-speed.pdf` | `data/time-series/bead/clockwise_*.parquet` | `code/bead-assay/bead_shock_curve_fits.ipynb` | Motors locked in clockwise rotation slow similarly, arguing that the response is upstream of motor direction switching. |
| Main Figure 6: sustained adaptation | `figures/osmoadaption-biophysics.pdf` | `outputs/figure-panels/figure-6a-adaptation-motor-speed.pdf` | `data/time-series/bead/adaption_*.parquet` | `code/bead-assay/adaptation_curve_fitting.ipynb` | During a longer shock, motor speed partly recovers over minutes, consistent with cellular adaptation and PMF restoration. |

## Supplemental Figures

| Supplemental result | Source artifact | Data | Plain-English takeaway |
|---|---|---|---|
| Individual sucrose motor traces | `figures/sucros_individual-cells_all.pdf` | `data/time-series/bead/sucrose_*.parquet` | Single-cell traces show the population trend is built from many motors, not one example. |
| Sucrose viscosity control | `figures/Viscosity-sucrose.pdf` | `data/Viscosity/Sucro/`, sucrose bead traces | Immediate motor slowdown is larger than expected from viscosity alone. |
| Sucrose decrease/recovery timescales | `figures/sucros-time-charc.pdf` | `data/time-series/bead/sucrose_*.parquet` | The speed decrease and recovery happen over seconds. |
| Cell-area response | `figures/change-in-cell-area.pdf` | `data/time-series/cell-area/*.parquet` | Cells shrink during osmotic shock and recover after return to base media. |
| 100 mM sucrose shock | `figures/100mM.pdf` | `data/time-series/bead/100mm_100mM.parquet` | A smaller shock still reduces motor speed. |
| Osmoprotectant condition | `figures/200-osmopro-short.pdf` | `data/time-series/bead/20mm_with_osmoprotectants_200mM.parquet` | Motor slowdown occurs even in the osmoprotectant condition measured here. |
| TMRM timescales | `figures/TMRM-timescales.pdf` | `data/time-series/tmrm/*.parquet` | Fluorescence changes on shock and recovery timescales consistent with membrane-potential dynamics. |
| Sorbitol, sodium, and clockwise timescales | `figures/Time-charact-sodium-sorb-clockwise.pdf` | sorbitol, sodium, and clockwise bead Parquet files | Fast motor slowdown is reproducible across control conditions. |
| Sorbitol viscosity control | `figures/Viscosity-Sorb.pdf` | `data/Viscosity/Sorb/`, sorbitol bead traces | Sorbitol motor slowdown also exceeds the viscosity-only prediction. |
| Combined sucrose/sorbitol corrected speed decrease | `figures/sucrose-sorb-combin-speed-decrease.pdf` | sucrose and sorbitol bead traces plus viscosity support data | After correcting for viscosity, motor slowdown still scales with osmotic strength. |

## Additional Figure Artifacts

The `figures/` folder also contains files that are not explicitly referenced by
the current main figure includes or supporting-information figure includes, such
as alternate versions or intermediate artifacts. Leave these files untouched
unless the manuscript source is intentionally updated in a separate task.
