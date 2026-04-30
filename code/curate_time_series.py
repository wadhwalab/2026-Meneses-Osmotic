"""Curate legacy analysis outputs into canonical time-series inputs.

This is a migration script for the repository cleanup. It reads the legacy
bead, TMRM, and cell-area outputs and writes the compact inputs used by the
downstream analysis scripts.

Bead traces are stored as compressed wide CSV files, one per assay/condition.
The bead manifest maps each biological trace to a column inside those files.

The sucrose bead traces are MATLAB v5 .mat files. A small reader is included so
the conversion does not require scipy during cleanup.
"""

from __future__ import annotations

import csv
import gzip
import math
import re
import shutil
import struct
import zlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "time-series"

DEFAULT_FPS = 300

MI_INT8 = 1
MI_UINT8 = 2
MI_INT16 = 3
MI_UINT16 = 4
MI_INT32 = 5
MI_UINT32 = 6
MI_SINGLE = 7
MI_DOUBLE = 9
MI_INT64 = 12
MI_UINT64 = 13
MI_MATRIX = 14
MI_COMPRESSED = 15

NUMERIC_TYPES = {
    MI_INT8: ("b", 1),
    MI_UINT8: ("B", 1),
    MI_INT16: ("h", 2),
    MI_UINT16: ("H", 2),
    MI_INT32: ("i", 4),
    MI_UINT32: ("I", 4),
    MI_SINGLE: ("f", 4),
    MI_DOUBLE: ("d", 8),
    MI_INT64: ("q", 8),
    MI_UINT64: ("Q", 8),
}


@dataclass(frozen=True)
class BeadSource:
    reader_kind: str
    read_path: Path
    assay: str
    osmolyte: str
    condition_mM: str
    cell_id: str
    rotation_direction: str
    fps: str
    source_kind: str
    source_path: str
    sign_adjustment: str = "none"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return cleaned or "unknown"


def token(text: str) -> str:
    return slug(text).replace("-", "_")


def parse_condition(text: str) -> str:
    match = re.search(r"(\d{2,4})\s*mM", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"(?:^|[^0-9])(\d{2,4})(?=merged|csv|_|-|\.|$)", text, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def parse_cell_id(text: str) -> str:
    match = re.search(r"cell[-_]?(\d+)", text, flags=re.IGNORECASE)
    return f"cell{match.group(1)}" if match else ""


def assay_metadata(assay: str) -> tuple[str, str]:
    mapping = {
        "100mM": ("sucrose", "CCW"),
        "20mM-with-osmoprotectants": ("osmoprotectants", "CCW"),
        "Adaption": ("sucrose", "CCW"),
        "Clockwise": ("sucrose", "CW"),
        "Sodium": ("sodium", "CCW"),
        "Sorbitol": ("sorbitol", "CCW"),
        "Sucrose": ("sucrose", "CCW"),
    }
    return mapping.get(assay, ("unknown", "unknown"))


def parse_fps(value: str) -> float:
    try:
        fps = float(value)
    except (TypeError, ValueError):
        return float(DEFAULT_FPS)
    return fps if fps > 0 else float(DEFAULT_FPS)


def read_legacy_speed_csv(path: Path) -> list[tuple[int, float]]:
    rows: list[tuple[int, float]] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        for raw in reader:
            if not raw:
                continue
            # Legacy files are typically pandas index CSVs with a header ",0".
            if len(raw) >= 2 and raw[0].strip():
                try:
                    frame = int(float(raw[0]))
                    value = float(raw[-1])
                except ValueError:
                    continue
                if math.isfinite(value):
                    rows.append((frame, value))
            elif len(raw) == 1:
                try:
                    value = float(raw[0])
                except ValueError:
                    continue
                if math.isfinite(value):
                    rows.append((len(rows), value))
    return rows


def read_frequency_csv(path: Path) -> list[tuple[int, float]]:
    rows: list[tuple[int, float]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                frame = int(float(row["frame"]))
                value = float(row["frequency_hz"])
            except (KeyError, ValueError):
                continue
            if math.isfinite(value):
                rows.append((frame, value))
    return rows


def read_tag(buffer: bytes, pos: int, endian: str) -> tuple[int, int, int, int, int]:
    raw = struct.unpack_from(endian + "I", buffer, pos)[0]
    small_size = raw >> 16
    if small_size:
        data_type = raw & 0xFFFF
        data_start = pos + 4
        data_end = data_start + small_size
        return data_type, small_size, data_start, data_end, pos + 8

    data_type, size = struct.unpack_from(endian + "II", buffer, pos)
    data_start = pos + 8
    data_end = data_start + size
    padding = (8 - (size % 8)) % 8
    return data_type, size, data_start, data_end, data_end + padding


def read_numeric_payload(payload: bytes, data_type: int, endian: str) -> list[float]:
    if data_type not in NUMERIC_TYPES:
        return []
    fmt, item_size = NUMERIC_TYPES[data_type]
    usable = len(payload) - (len(payload) % item_size)
    if usable <= 0:
        return []
    unpacker = struct.iter_unpack(endian + fmt, payload[:usable])
    return [float(item[0]) for item in unpacker]


def parse_mat_matrix(content: bytes, endian: str) -> tuple[str, list[float]]:
    pos = 0
    _, _, _, _, pos = read_tag(content, pos, endian)  # array flags
    _, _, dim_start, dim_end, pos = read_tag(content, pos, endian)
    _ = read_numeric_payload(content[dim_start:dim_end], MI_INT32, endian)

    _, _, name_start, name_end, pos = read_tag(content, pos, endian)
    name = content[name_start:name_end].decode("latin1").strip("\x00")

    data_type, _, real_start, real_end, _ = read_tag(content, pos, endian)
    values = read_numeric_payload(content[real_start:real_end], data_type, endian)
    return name, values


def parse_mat_elements(buffer: bytes, endian: str, out: dict[str, list[float]]) -> None:
    pos = 0
    while pos + 8 <= len(buffer):
        data_type, _, start, end, next_pos = read_tag(buffer, pos, endian)
        if next_pos <= pos:
            break
        if end > len(buffer) or data_type not in {MI_COMPRESSED, MI_MATRIX}:
            # Some legacy MATLAB files contain non-element trailing bytes after a
            # valid compressed matrix. Stop rather than interpreting those bytes
            # as additional tags.
            break
        if data_type == MI_COMPRESSED:
            parse_mat_elements(zlib.decompress(buffer[start:end]), endian, out)
        elif data_type == MI_MATRIX:
            name, values = parse_mat_matrix(buffer[start:end], endian)
            if name and values:
                out[name] = values
        pos = next_pos


def load_mat_v5(path: Path) -> dict[str, list[float]]:
    data = path.read_bytes()
    if len(data) < 128 or b"MATLAB 5.0 MAT-file" not in data[:128]:
        raise ValueError(f"Unsupported MAT file format: {path}")
    endian_marker = data[126:128]
    endian = "<" if endian_marker == b"IM" else ">"
    values: dict[str, list[float]] = {}
    parse_mat_elements(data[128:], endian, values)
    return values


def median(values: list[float]) -> float:
    clean = sorted(v for v in values if math.isfinite(v))
    if not clean:
        return 0.0
    mid = len(clean) // 2
    if len(clean) % 2:
        return clean[mid]
    return (clean[mid - 1] + clean[mid]) / 2


def discover_legacy_bead_csvs() -> list[BeadSource]:
    sources: list[BeadSource] = []
    base = DATA / "Bead-assays"
    for source in sorted(base.glob("*/speeds/**/*.csv")):
        parts = source.relative_to(base).parts
        assay = parts[0]
        condition = parse_condition(source.parent.name) or parse_condition(str(source))
        osmolyte, rotation_direction = assay_metadata(assay)
        sources.append(
            BeadSource(
                reader_kind="legacy_csv",
                read_path=source,
                assay=assay,
                osmolyte=osmolyte,
                condition_mM=condition,
                cell_id=parse_cell_id(source.stem),
                rotation_direction=rotation_direction,
                fps=str(DEFAULT_FPS),
                source_kind="legacy_csv",
                source_path=rel(source),
            )
        )
    return sources


def discover_legacy_sucrose_mats() -> list[BeadSource]:
    sources: list[BeadSource] = []
    base = DATA / "Bead-assays" / "Sucrose"
    for source in sorted(base.rglob("*.mat")):
        if "freq" not in source.name.lower():
            continue
        sources.append(
            BeadSource(
                reader_kind="legacy_mat",
                read_path=source,
                assay="Sucrose",
                osmolyte="sucrose",
                condition_mM=parse_condition(str(source)),
                cell_id=parse_cell_id(str(source)),
                rotation_direction="CCW",
                fps=str(DEFAULT_FPS),
                source_kind="legacy_mat",
                source_path=rel(source),
            )
        )
    return sources


def discover_existing_per_trace_bead_csvs() -> list[BeadSource]:
    manifest_path = OUT / "bead" / "manifest.csv"
    if not manifest_path.exists():
        return []

    with manifest_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if "column_name" in (reader.fieldnames or []):
            return []
        rows = list(reader)

    sources: list[BeadSource] = []
    for row in rows:
        read_path = ROOT / row["path"]
        if not read_path.exists():
            continue
        sources.append(
            BeadSource(
                reader_kind="canonical_csv",
                read_path=read_path,
                assay=row["assay"],
                osmolyte=row["osmolyte"],
                condition_mM=row["condition_mM"],
                cell_id=row["cell_id"],
                rotation_direction=row["rotation_direction"],
                fps=row["fps"],
                source_kind=row["source_kind"],
                source_path=row["source_path"],
                sign_adjustment=row["sign_adjustment"],
            )
        )
    return sources


def read_bead_source(source: BeadSource) -> tuple[list[tuple[int, float]], str]:
    if source.reader_kind == "legacy_csv":
        return read_legacy_speed_csv(source.read_path), source.sign_adjustment
    if source.reader_kind == "canonical_csv":
        return read_frequency_csv(source.read_path), source.sign_adjustment
    if source.reader_kind == "legacy_mat":
        variables = load_mat_v5(source.read_path)
        if "F" not in variables:
            return [], source.sign_adjustment
        values = variables["F"]
        sign_adjustment = "none"
        if median(values) < 0:
            values = [-v for v in values]
            sign_adjustment = "inverted"
        trace = [(frame, value) for frame, value in enumerate(values) if math.isfinite(value)]
        return trace, sign_adjustment
    raise ValueError(f"Unknown bead source reader: {source.reader_kind}")


def bead_condition_path(source: BeadSource) -> Path:
    condition = source.condition_mM or "unknown"
    return OUT / "bead" / f"{token(source.assay)}_{condition}mM.csv.gz"


def unique_column_name(base: str, used: dict[str, int]) -> str:
    clean = token(base) if base else "trace"
    count = used.get(clean, 0) + 1
    used[clean] = count
    return clean if count == 1 else f"{clean}_{count}"


def write_wide_bead_files(sources: list[BeadSource]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[BeadSource]] = defaultdict(list)
    for source in sources:
        grouped[(source.assay, source.osmolyte, source.condition_mM)].append(source)

    manifest_rows: list[dict[str, str]] = []
    for _, group in sorted(grouped.items()):
        target = bead_condition_path(group[0])
        target.parent.mkdir(parents=True, exist_ok=True)
        group_fps = parse_fps(group[0].fps)
        used_columns: dict[str, int] = {}
        prepared: list[tuple[BeadSource, str, dict[int, float], str]] = []
        all_frames: set[int] = set()

        for source in group:
            trace, sign_adjustment = read_bead_source(source)
            if not trace:
                continue
            values_by_frame = {frame: value for frame, value in trace if math.isfinite(value)}
            if not values_by_frame:
                continue
            column_name = unique_column_name(source.cell_id or Path(source.source_path).stem, used_columns)
            prepared.append((source, column_name, values_by_frame, sign_adjustment))
            all_frames.update(values_by_frame)

        if not prepared:
            continue

        with gzip.open(target, "wt", newline="", compresslevel=6) as handle:
            writer = csv.writer(handle)
            writer.writerow(["frame", "time_s", *[item[1] for item in prepared]])
            for frame in sorted(all_frames):
                row: list[object] = [frame, frame / group_fps]
                for _, _, values_by_frame, _ in prepared:
                    row.append(values_by_frame.get(frame, ""))
                writer.writerow(row)

        for source, column_name, _, sign_adjustment in prepared:
            manifest_rows.append(
                {
                    "path": rel(target),
                    "column_name": column_name,
                    "assay": source.assay,
                    "osmolyte": source.osmolyte,
                    "condition_mM": source.condition_mM,
                    "cell_id": source.cell_id,
                    "rotation_direction": source.rotation_direction,
                    "fps": source.fps,
                    "source_kind": source.source_kind,
                    "source_path": source.source_path,
                    "sign_adjustment": sign_adjustment,
                }
            )
    return manifest_rows


def copy_condition_csvs(source_dir: Path, target_dir: Path, value_column: str) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.glob("*.csv")):
        if source.name.endswith("_dff.csv"):
            continue
        if value_column == "area" and source.name.startswith("."):
            continue
        condition = parse_condition(source.name)
        if source.name.lower().startswith("control"):
            name = "control.csv"
        elif condition:
            name = f"{condition}mM.csv"
        else:
            name = f"{slug(source.stem)}.csv"
        shutil.copyfile(source, target_dir / name)


def write_manifest(rows: list[dict[str, str]]) -> None:
    manifest_path = OUT / "bead" / "manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "path",
        "column_name",
        "assay",
        "osmolyte",
        "condition_mM",
        "cell_id",
        "rotation_direction",
        "fps",
        "source_kind",
        "source_path",
        "sign_adjustment",
    ]
    with manifest_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    bead_sources = discover_legacy_bead_csvs() + discover_legacy_sucrose_mats()
    if not bead_sources:
        bead_sources = discover_existing_per_trace_bead_csvs()

    if bead_sources:
        manifest_rows = write_wide_bead_files(bead_sources)
        write_manifest(manifest_rows)
        print(f"Wrote {len(manifest_rows)} bead traces across compressed condition files")
    else:
        print("No bead trace sources found; existing bead inputs were left unchanged")

    copy_condition_csvs(
        DATA / "TMRM-results" / "combined",
        OUT / "tmrm",
        value_column="fluorescence",
    )
    copy_condition_csvs(
        DATA / "Cell-area" / "Analysis_combined",
        OUT / "cell-area",
        value_column="area",
    )

    print(f"Wrote TMRM files to {rel(OUT / 'tmrm')}")
    print(f"Wrote cell-area files to {rel(OUT / 'cell-area')}")


if __name__ == "__main__":
    main()
