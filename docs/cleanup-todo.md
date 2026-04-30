# Cleanup To-Do List

## 1. Explore Bead-Assay Subsampling

- Determine the minimum temporal resolution needed for downstream fits and plots.
- Compare full-rate, binned, and downsampled traces.
- Quantify effects on tau, amplitude, plateau, and population summaries.
- Decide whether to store full-rate data, reduced data, or both.

## 2. Investigate Reducing `.git` Bloat

- Confirm which historical paths dominate `.git` size.
- Test `git filter-repo` or BFG on a throwaway clone.
- Purge removed upstream paths from history.
- Run `git gc --prune=now --aggressive`.
- Verify post-rewrite clone size.
- Decide force-push and archival strategy before changing remote history.

## 3. Evaluate Better Bead-Assay Storage Formats

- Compare current wide `.csv.gz` files against:
  - `.csv.zst`
  - Parquet
  - HDF5
  - NumPy `.npz`
  - Feather/Arrow
- Measure size, read speed, dependency burden, and notebook usability.
- Decide the canonical format and whether to keep CSV export utilities.

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
