from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "creating_ids.py"
    spec = importlib.util.spec_from_file_location("creating_ids", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


creating_ids = _load_module()
REPO_ROOT = Path(__file__).resolve().parents[1]
SHAPE_YAML = REPO_ROOT / "SHAPE" / "rnastruct00001.yaml"
EXPECTED_IDS = [
    "GSM4333255",
    "GSM4333256",
    "GSM4333257",
    "GSM4333258",
    "GSM4333259",
    "GSM4333260",
    "GSM4333261",
    "GSM4333262",
    "GSM4333263",
    "GSM4333264",
]


def test_run_accessions_from_list_extracts_accession_values():
    with SHAPE_YAML.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    run_accessions = data["raw_data"]["run_accessions"]
    assert creating_ids._run_accessions_from_list(run_accessions) == EXPECTED_IDS


def test_extract_ids_reads_raw_data_run_accessions_only():
    with SHAPE_YAML.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert creating_ids.extract_ids(data) == (EXPECTED_IDS, "run_accessions")


def test_main_writes_csv_and_returns_zero(tmp_path, monkeypatch, capsys):
    csv_path = tmp_path / "ids.csv"

    monkeypatch.setattr(
        "sys.argv",
        ["creating_ids.py", str(SHAPE_YAML), str(csv_path)],
    )

    rc = creating_ids.main()

    assert rc == 0
    assert csv_path.read_text(encoding="utf-8") == "\n".join(EXPECTED_IDS) + "\n"
    assert "Wrote 10 IDs from run_accessions." in capsys.readouterr().err
