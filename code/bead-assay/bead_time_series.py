"""Helpers for bead analysis notebooks that start from compact time series.

The canonical bead data live in ``data/time-series/bead`` as 0.1 s mean-binned
wide Parquet files: one file per assay/condition and one column per trace. The
original analysis notebooks expect a legacy ``speeds/<condition>/*.csv`` tree.
The helpers below bridge those two layouts without restoring the bulky upstream
data directories.
"""

from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
BEAD_DIR = ROOT / "data" / "time-series" / "bead"
OUTPUT_ROOT = ROOT / "outputs" / "bead"
DEFAULT_FPS = 300
TIME_BIN_S = 0.1
FRAME_REFERENCE_FPS = 300


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", str(text)).strip("-").lower()
    return cleaned or "unknown"


def load_manifest() -> list[dict[str, str]]:
    with (BEAD_DIR / "manifest.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


def _matches(row: dict[str, str], key: str, value: object | None) -> bool:
    if value is None:
        return True
    return str(row[key]).lower() == str(value).lower()


def select_manifest(
    *,
    assay: str | None = None,
    osmolyte: str | None = None,
    condition_mM: int | str | None = None,
    rotation_direction: str | None = None,
) -> list[dict[str, str]]:
    return [
        row
        for row in load_manifest()
        if _matches(row, "assay", assay)
        and _matches(row, "osmolyte", osmolyte)
        and _matches(row, "condition_mM", condition_mM)
        and _matches(row, "rotation_direction", rotation_direction)
    ]


def _tree_name(
    *,
    assay: str | None,
    osmolyte: str | None,
    condition_mM: int | str | None,
    rotation_direction: str | None,
) -> str:
    parts = [
        part
        for part in [assay, osmolyte, condition_mM, rotation_direction]
        if part is not None and str(part) != ""
    ]
    return "_".join(_slug(str(part)) for part in parts) or "all"


def _group_by_path(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["path"], []).append(row)
    return grouped


def _condition_label(row: dict[str, str]) -> str:
    condition = row.get("condition_mM") or "unknown"
    return f"{condition}mM"


def _legacy_csv_name(row: dict[str, str]) -> str:
    cell_id = row.get("cell_id") or row["column_name"]
    return f"freq-{_slug(cell_id)}.csv"


def median_kernel_size(time_s, window_s: float = 1.0) -> int:
    """Return an odd sample count spanning approximately ``window_s`` seconds."""
    import numpy as np

    time = np.asarray(time_s, dtype=float)
    dt = np.diff(time[np.isfinite(time)])
    dt = dt[dt > 0]
    if len(dt) == 0:
        return 1
    size = max(1, int(round(window_s / float(np.median(dt)))))
    return size if size % 2 == 1 else size + 1


def legacy_speed_tree(
    *,
    assay: str | None = None,
    osmolyte: str | None = None,
    condition_mM: int | str | None = None,
    rotation_direction: str | None = None,
    output_root: Path | None = None,
    force: bool = False,
) -> Path:
    """Materialize a legacy per-trace speed tree from compact canonical inputs.

    This is a compatibility bridge for older notebook cells. It does not restore
    raw bead tracking files; it only rewrites the curated Parquet traces into the
    two-column CSV shape those cells expect.

    The returned directory contains condition subfolders such as ``200mM``.
    Files are written as pandas-style two-column CSVs with an index column and a
    column named ``0``, matching the shape used by the original notebooks.
    The first column stores the original 300 Hz frame reference at each 0.1 s
    bin midpoint, so older code that computes ``frame / 300`` still gets time
    in seconds.
    """
    rows = select_manifest(
        assay=assay,
        osmolyte=osmolyte,
        condition_mM=condition_mM,
        rotation_direction=rotation_direction,
    )
    if not rows:
        raise FileNotFoundError("No bead traces matched the requested filters.")

    root = (output_root or OUTPUT_ROOT / "legacy-speed-tree") / _tree_name(
        assay=assay,
        osmolyte=osmolyte,
        condition_mM=condition_mM,
        rotation_direction=rotation_direction,
    )
    if force and root.exists():
        shutil.rmtree(root)
    if root.exists() and any(root.rglob("*.csv")):
        return root

    root.mkdir(parents=True, exist_ok=True)
    for relative_path, path_rows in _group_by_path(rows).items():
        source = ROOT / relative_path
        selected_by_column = {row["column_name"]: row for row in path_rows}
        table = pq.read_table(source, columns=["frame", *selected_by_column])
        source_data = table.to_pydict()
        frames = source_data["frame"]
        handles: dict[str, object] = {}
        writers: dict[str, csv.writer] = {}
        try:
            for row in path_rows:
                target_dir = root / _condition_label(row)
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / _legacy_csv_name(row)
                handle = target.open("w", newline="")
                writer = csv.writer(handle)
                writer.writerow(["", "0"])
                handles[row["column_name"]] = handle
                writers[row["column_name"]] = writer

            for idx, frame in enumerate(frames):
                for column_name in selected_by_column:
                    value = source_data[column_name][idx]
                    if value is not None:
                        writers[column_name].writerow([frame, value])
        finally:
            for handle in handles.values():
                handle.close()
    return root


def legacy_condition_folder(
    *,
    condition_mM: int | str,
    assay: str | None = None,
    osmolyte: str | None = None,
    rotation_direction: str | None = None,
    output_root: Path | None = None,
    force: bool = False,
) -> Path:
    root = legacy_speed_tree(
        assay=assay,
        osmolyte=osmolyte,
        condition_mM=condition_mM,
        rotation_direction=rotation_direction,
        output_root=output_root,
        force=force,
    )
    condition_dir = root / f"{condition_mM}mM"
    if not condition_dir.exists():
        raise FileNotFoundError(f"Expected materialized folder not found: {condition_dir}")
    return condition_dir


def read_legacy_speed_csv(path: str | Path):
    """Read a materialized trace CSV into a two-column pandas DataFrame."""
    import pandas as pd

    df = pd.read_csv(path)
    if "Unnamed: 0" in df.columns and "0" in df.columns:
        out = df[["Unnamed: 0", "0"]].copy()
        out.columns = ["frame", "frequency_hz"]
        return out.apply(pd.to_numeric, errors="coerce").dropna()
    out = pd.read_csv(path, header=None)
    out = out.apply(pd.to_numeric, errors="coerce").dropna()
    out.columns = ["frame", "frequency_hz"]
    return out


def iter_condition_traces(
    *,
    assay: str | None = None,
    osmolyte: str | None = None,
    condition_mM: int | str | None = None,
    rotation_direction: str | None = None,
):
    """Yield ``(metadata, trace_dataframe)`` pairs from compact wide files."""
    import pandas as pd

    rows = select_manifest(
        assay=assay,
        osmolyte=osmolyte,
        condition_mM=condition_mM,
        rotation_direction=rotation_direction,
    )
    for relative_path, path_rows in _group_by_path(rows).items():
        source = ROOT / relative_path
        wide = pd.read_parquet(source)
        for row in path_rows:
            column = row["column_name"]
            trace = wide[["frame", "time_s", column]].dropna().copy()
            trace = trace.rename(columns={column: "frequency_hz"})
            yield row, trace
