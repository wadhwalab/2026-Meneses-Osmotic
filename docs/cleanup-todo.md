# Cleanup To-Do List

## 1. Explore Bead-Assay Subsampling

- Status: evaluated in `docs/bead-subsampling-analysis.md`.
- Implemented: bead Parquet files now store 0.1 s mean-binned time series.
- Keep full 300 Hz bead traces outside Git only if future sub-second motor
  fluctuation analysis is needed.

## 2. Investigate Reducing `.git` Bloat

- Confirm which historical paths dominate `.git` size.
- Test `git filter-repo` or BFG on a throwaway clone.
- Purge removed upstream paths from history.
- Run `git gc --prune=now --aggressive`.
- Verify post-rewrite clone size.
- Decide force-push and archival strategy before changing remote history.

## 3. Validate Bead-Assay Storage Format

- Parquet is now the canonical working format for time-series data.
- Keep measuring alternatives only if size or usability becomes a problem:
  - `.csv.zst`
  - HDF5
  - NumPy `.npz`
  - Feather/Arrow
- Measure size, read speed, dependency burden, and notebook usability.
- Decide whether to keep CSV export utilities for collaborators who prefer text files.

## 4. Run and Test the Full Codebase

- Set up a clean environment with required dependencies.
- Run TMRM scripts.
- Run cell-area scripts.
- Run bead notebooks/scripts end to end where possible.
- Capture expected outputs and failures.
- Add lightweight smoke tests for key scripts and helpers.

## 5. Review Every Code File and Notebook Individually

- Identify each file's purpose, inputs, outputs, and whether it is upstream or downstream.
- Remove dead code and stale absolute paths.
- Add short usage notes at the top of each script/notebook.
- Standardize repo-relative paths.
- Clear notebook outputs.
- Document required dependencies.
- Mark notebooks as maintained, archival, or deprecated.

## 6. Document the Cleaned Workflow

- Update `README.md` with the final analysis path.
- Add a data layout guide for `data/time-series`.
- Add a "how to regenerate outputs" section.
- Add a history-rewrite note and safety checklist.
- Add expected repo size targets after cleanup.
