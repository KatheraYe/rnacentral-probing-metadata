from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "creating_ids.py"
    spec = importlib.util.spec_from_file_location("creating_ids", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


creating_ids = _load_module()


def test_as_list_handles_none_and_whitespace():
    assert creating_ids._as_list(None) == []
    assert creating_ids._as_list("   ") == []


def test_as_list_normalizes_scalars_and_lists():
    assert creating_ids._as_list("SRR0001") == ["SRR0001"]
    assert creating_ids._as_list(["SRR0001", None, "  ", 123]) == ["SRR0001", "123"]


def test_extract_ids_prefers_run_accessions_over_accession():
    data = {
        "accession": ["GSE0001"],
        "run_accessions": ["SRR0001", "SRR0002"],
    }
    assert creating_ids.extract_ids(data) == (["SRR0001", "SRR0002"], "run_accessions")


def test_extract_ids_finds_nested_values():
    data = {"outer": {"inner": {"accession": "GSE0001"}}}
    assert creating_ids.extract_ids(data) == (["GSE0001"], "accession")


def test_extract_ids_returns_none_when_missing():
    assert creating_ids.extract_ids({"a": {"b": []}}) is None


def test_main_writes_csv_and_returns_zero(tmp_path, monkeypatch, capsys):
    yaml_path = tmp_path / "input.yaml"
    csv_path = tmp_path / "ids.csv"
    yaml_path.write_text("run_accessions:\n  - SRR100\n  - SRR200\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        ["creating_ids.py", str(yaml_path), str(csv_path)],
    )

    rc = creating_ids.main()

    assert rc == 0
    assert csv_path.read_text(encoding="utf-8") == "SRR100\nSRR200\n"
    assert "Wrote 2 IDs from run_accessions." in capsys.readouterr().err


def test_main_returns_one_when_no_ids_found(tmp_path, monkeypatch, capsys):
    yaml_path = tmp_path / "input.yaml"
    csv_path = tmp_path / "ids.csv"
    yaml_path.write_text("title: only metadata\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        ["creating_ids.py", str(yaml_path), str(csv_path)],
    )

    rc = creating_ids.main()

    assert rc == 1
    assert not csv_path.exists()
    assert "No run_accessions or accession found in YAML." in capsys.readouterr().err
