from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "check_metadata_uniqueness.py"
    spec = importlib.util.spec_from_file_location("check_metadata_uniqueness", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_uniqueness = _load_module()


def _write_yaml(path: Path, dataset_id: str, run_accessions: list[str]) -> None:
    runs = "\n".join(
        [
            "    - accession: {acc}\n"
            "      sample_name: sample_{i}\n"
            "      cell_line: HeLa\n"
            "      condition: treated\n"
            "      replicate: 1".format(acc=acc, i=i)
            for i, acc in enumerate(run_accessions, start=1)
        ]
    )
    path.write_text(
        (
            f"dataset_id: {dataset_id}\n"
            "organism:\n"
            "  name: Homo sapiens\n"
            "  genome_build: hg38\n"
            "publication:\n"
            "  doi: 10.1000/test\n"
            "raw_data:\n"
            "  repository: GEO\n"
            "  accession: GSE123456\n"
            "  run_accessions:\n"
            f"{runs}\n"
        ),
        encoding="utf-8",
    )


def test_find_uniqueness_issues_returns_empty_for_unique_values(tmp_path):
    shape_dir = tmp_path / "SHAPE"
    dms_dir = tmp_path / "DMS"
    shape_dir.mkdir()
    dms_dir.mkdir()

    shape_file = shape_dir / "rnastruct00001.yaml"
    dms_file = dms_dir / "rnastruct00002.yaml"
    _write_yaml(shape_file, "rnastruct00001", ["GSM1001"])
    _write_yaml(dms_file, "rnastruct00002", ["GSM2001"])

    paths = check_uniqueness.collect_metadata_files(tmp_path, ["SHAPE", "DMS"])
    issues = check_uniqueness.find_uniqueness_issues(paths)

    assert issues == []


def test_find_uniqueness_issues_reports_duplicate_dataset_id(tmp_path):
    shape_dir = tmp_path / "SHAPE"
    dms_dir = tmp_path / "DMS"
    shape_dir.mkdir()
    dms_dir.mkdir()

    shape_file = shape_dir / "rnastruct00001.yaml"
    dms_file = dms_dir / "rnastruct00002.yaml"
    _write_yaml(shape_file, "rnastruct99999", ["GSM1001"])
    _write_yaml(dms_file, "rnastruct99999", ["GSM2001"])

    paths = check_uniqueness.collect_metadata_files(tmp_path, ["SHAPE", "DMS"])
    issues = check_uniqueness.find_uniqueness_issues(paths)

    assert any("Duplicate dataset_id 'rnastruct99999'" in issue for issue in issues)


def test_find_uniqueness_issues_reports_duplicate_run_accession(tmp_path):
    shape_dir = tmp_path / "SHAPE"
    dms_dir = tmp_path / "DMS"
    shape_dir.mkdir()
    dms_dir.mkdir()

    shape_file = shape_dir / "rnastruct00001.yaml"
    dms_file = dms_dir / "rnastruct00002.yaml"
    _write_yaml(shape_file, "rnastruct00001", ["GSM1234"])
    _write_yaml(dms_file, "rnastruct00002", ["GSM1234"])

    paths = check_uniqueness.collect_metadata_files(tmp_path, ["SHAPE", "DMS"])
    issues = check_uniqueness.find_uniqueness_issues(paths)

    assert any("Duplicate run accession 'GSM1234'" in issue for issue in issues)
