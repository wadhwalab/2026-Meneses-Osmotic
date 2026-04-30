from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


SUPPORTED_FILES = [
    ROOT / "code" / "TMRM-anaylsis" / "analyze_tmrm_population_dff.py",
    ROOT / "code" / "TMRM-anaylsis" / "analyze_tmrm_single_condition_dff.py",
    ROOT / "code" / "Cell-area-anaylsis" / "analyze_cell_area_population_dff.py",
    ROOT / "code" / "Cell-area-anaylsis" / "analyze_cell_area_single_condition_dff.py",
    ROOT / "code" / "bead-assay" / "plot_viscosity_control.py",
    ROOT / "code" / "bead-assay" / "sucrose_shock_analysis.ipynb",
    ROOT / "code" / "bead-assay" / "bead_shock_curve_fits.ipynb",
    ROOT / "code" / "bead-assay" / "adaptation_curve_fitting.ipynb",
]

OLD_NAMES = [
    ROOT / "code" / "TMRM-anaylsis" / "021_MergeMultiDFF.py",
    ROOT / "code" / "TMRM-anaylsis" / "019 FJF_Fo_TMRM-post-analysis-DeltaF_Fo.py",
    ROOT / "code" / "Cell-area-anaylsis" / "021-2 MergeMultiDFF_AREA__.py",
    ROOT / "code" / "Cell-area-anaylsis" / "019-2 F_Fo_for_AREA_TMRM.py",
    ROOT / "code" / "bead-assay" / "Viscosity.py",
    ROOT / "code" / "bead-assay" / "sucrose-shock-plotting.ipynb",
    ROOT / "code" / "bead-assay" / "plot-and-curve-fit.ipynb",
    ROOT / "code" / "bead-assay" / "adaption-curve-fitting.ipynb",
]


def test_supported_files_were_renamed() -> None:
    for path in SUPPORTED_FILES:
        assert path.exists(), path
    for path in OLD_NAMES:
        assert not path.exists(), path


def test_bead_manifest_matches_parquet_files() -> None:
    manifest_path = ROOT / "data" / "time-series" / "bead" / "manifest.csv"
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    required = {
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
        "time_bin_s",
        "reduction",
        "frame_reference_fps",
    }
    assert set(rows[0]) == required

    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        assert row["time_bin_s"] == "0.1"
        assert row["reduction"] == "mean_bin"
        assert row["frame_reference_fps"] == "300"
        grouped.setdefault(row["path"], []).append(row)

    for relative_path, path_rows in grouped.items():
        parquet_path = ROOT / relative_path
        assert parquet_path.exists(), parquet_path
        df = pd.read_parquet(parquet_path)
        assert {"frame", "time_s"}.issubset(df.columns)
        for row in path_rows:
            assert row["column_name"] in df.columns


def test_tmrm_and_cell_area_schemas() -> None:
    expected = {
        ROOT / "data" / "time-series" / "tmrm": {"track_id", "frame", "fluorescence"},
        ROOT / "data" / "time-series" / "cell-area": {"track_id", "frame", "area"},
    }
    for folder, columns in expected.items():
        files = sorted(folder.glob("*.parquet"))
        assert files, folder
        for path in files:
            df = pd.read_parquet(path)
            assert set(df.columns) == columns
            assert df["track_id"].nunique() == 40
            assert len(df) == 3240


def test_notebooks_are_cleaned_for_time_series_workflow() -> None:
    for path in ROOT.glob("code/bead-assay/*.ipynb"):
        nb = json.loads(path.read_text(encoding="utf-8"))
        assert nb["cells"][0]["cell_type"] == "markdown"
        assert "curated time-series data" in "".join(nb["cells"][0]["source"])
        for cell in nb["cells"]:
            if cell.get("cell_type") == "code":
                assert cell.get("execution_count") is None
                assert cell.get("outputs") == []


def test_no_hardcoded_local_absolute_paths() -> None:
    tokens = [
        "/" + "Users/",
        "ASU " + "Dropbox",
        "C:" + "\\Users",
        "\\" + "Users\\",
        "Osmolarity-" + "mesurments",
    ]
    suffixes = {".py", ".ipynb", ".md", ".txt", ".yml", ".yaml", ".csv"}
    scanned = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in {".git", "figures", "__pycache__"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        for token in tokens:
            assert token not in text, f"{token!r} found in {path}"
    assert scanned > 0
