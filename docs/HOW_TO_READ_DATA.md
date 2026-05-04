# How To Read The Data

The repository starts from curated, downstream time-series data. In plain terms:
the raw microscope movies and image-segmentation files have already been turned
into tables of motor speed, fluorescence, or cell area over time.

## File Formats

- `.parquet`: compact table format used for the canonical time-series data. It
  is efficient and reliable for numeric data, but usually needs Python, R, or a
  spreadsheet tool with Parquet support.
- `.csv`: plain text table that can be opened by most spreadsheet programs.
  These are used for manifests, processed outputs, and quick-look summaries.
- `.xlsx`: spreadsheet files containing osmolarity and viscosity support data.
- `.pdf`: figure files. The original paper figures live in `manuscript/figures/`;
  code-generated panel outputs live in `outputs/figure-panels/`.

## Bead Motor-Speed Data

Location: `data/time-series/bead/`

These files contain the rotation speed of beads attached to bacterial flagellar
motors.

Each bead Parquet file has:

| Column | Meaning | Units |
|---|---|---|
| `frame` | Original 300 Hz frame reference at the center of each time bin. | frame number |
| `time_s` | Time after recording started. Use this as the main time axis. | seconds |
| `cell1`, `cell2`, etc. | Rotation-frequency trace for one cell/motor. | Hz, rotations per second |

Important processing:

- The original high-speed motor traces were reduced to `0.1 s` mean-binned time
  series to keep the repository compact.
- The binning preserves the shock, recovery, and population results used in the
  paper; see `docs/bead-subsampling-analysis.md`.
- Some notebook code still computes time as `frame / 300`; this remains valid
  because `frame` preserves the 300 Hz reference.

Metadata:

`data/time-series/bead/manifest.csv` explains every bead trace.

| Manifest column | Plain-English meaning |
|---|---|
| `path` | Which Parquet file contains the trace. |
| `column_name` | Which column in that file contains the trace. |
| `assay` | Experimental condition group, such as sucrose, sorbitol, sodium buffer, clockwise motors, or adaptation. |
| `osmolyte` | Solute used to create the osmotic shock. |
| `condition_mM` | Added osmolyte concentration. |
| `cell_id` | Identifier for one measured cell/motor. |
| `rotation_direction` | Whether the motor was counterclockwise (`CCW`) or clockwise (`CW`). |
| `fps` | Original acquisition rate. |
| `source_kind` and `source_path` | Historical lineage of the curated trace. Raw upstream files are not included. |
| `sign_adjustment` | Whether a trace direction was adjusted during curation. Some speed data were originally sign-inverted due to the convention used in earlier analysis. |
| `time_bin_s` | Width of the time bin used in the committed data. |
| `reduction` | How each bin was summarized; here, a mean. |
| `frame_reference_fps` | Frame-rate reference retained for compatibility. |

## TMRM Fluorescence Data

Location: `data/time-series/tmrm/`

TMRM is a fluorescent dye whose signal changes with membrane potential. These
data provide an independent check that osmotic shock depolarizes the cell.

Each Parquet file has:

| Column | Meaning | Units |
|---|---|---|
| `track_id` | Identifier for one tracked cell. | unitless |
| `frame` | Frame number in the fluorescence time series. | frame number |
| `fluorescence` | Curated intracellular-to-background fluorescence ratio. | ratio, unitless |

Maintained scripts add:

| Output column | Meaning | Units |
|---|---|---|
| `time_s` | Time after imaging started. The scripts use 5 seconds per frame. | seconds |
| `dff` | Baseline-normalized change in TMRM signal. Negative values mean signal decreased after shock. | fraction |

Important processing:

- The default shock frame is `35`, corresponding to `175 s`.
- The baseline is the 10 frames before shock.
- The current script normalizes the ratio relative to signal above background,
  storing the result in a column called `dff`.

## Cell-Area Data

Location: `data/time-series/cell-area/`

These files show how cell size changes during osmotic shock. A rapid decrease in
area is expected when external osmolarity increases and water leaves the cell.

Each Parquet file has:

| Column | Meaning | Units |
|---|---|---|
| `track_id` | Identifier for one tracked cell. | unitless |
| `frame` | Frame number in the area time series. | frame number |
| `area` | Segmented cell area in the microscope image. | pixels |

Maintained scripts add:

| Output column | Meaning | Units |
|---|---|---|
| `time_s` | Time after imaging started. The scripts use 5 seconds per frame. | seconds |
| `dff` | Baseline-normalized area change, equivalent to DeltaA/A0. Negative values mean the cell got smaller. | fraction |

## Osmolarity And Viscosity Support Data

Locations:

- `data/Osmolarity-readings/`
- `data/Viscosity/`

Osmolarity files record how much total solute is present in each shock solution.
The paper uses change in osmolarity to compare shock strengths across sucrose,
sorbitol, and sodium phosphate buffer conditions.

Viscosity files estimate the motor-speed decrease expected simply because a
more viscous liquid is harder for the bead to rotate through. This is the
viscosity-only prediction. The key biological result is that measured motor
slowdown is larger than viscosity alone can explain during the immediate shock,
supporting a PMF decrease rather than a purely mechanical drag effect.

## Interpreting Normalized Values

- A bead motor speed near `1` after normalization means the motor is rotating at
  its pre-shock baseline speed.
- A bead motor speed below `1` means the motor slowed down.
- A negative TMRM `dff` means fluorescence decreased, consistent with
  depolarization.
- A negative cell-area `dff` means cells became smaller during the shock.
- Error bands in population plots usually show standard error (`SE` or `SEM`),
  describing uncertainty in the mean trace.
