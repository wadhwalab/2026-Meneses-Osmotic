"""Helpers for bead analysis notebooks that now start from compact time series.

The canonical bead data live in ``data/time-series/bead`` as compressed wide
CSV files: one file per assay/condition and one column per trace. The original
analysis notebooks expect a legacy ``speeds/<condition>/*.csv`` tree. The
helpers below bridge those two layouts without restoring the bulky upstream
data directories.
"""

from __future__ import annotations

import csv
import gzip
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BEAD_DIR = ROOT / "data" / "time-series" / "bead"
OUTPUT_ROOT = ROOT / "outputs" / "bead"
DEFAULT_FPS = 300


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


def _open_csv(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", newline="")
    return path.open(newline="")


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

    The returned directory contains condition subfolders such as ``200mM``.
    Files are written as pandas-style two-column CSVs with an index column and a
    column named ``0``, matching the shape used by the original notebooks.
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

            with _open_csv(source) as handle:
                reader = csv.DictReader(handle)
                for source_row in reader:
                    frame = source_row["frame"]
                    for column_name, row in selected_by_column.items():
                        value = source_row.get(column_name, "")
                        if value != "":
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
        wide = pd.read_csv(source)
        for row in path_rows:
            column = row["column_name"]
            trace = wide[["frame", "time_s", column]].dropna().copy()
            trace = trace.rename(columns={column: "frequency_hz"})
            yield row, trace
