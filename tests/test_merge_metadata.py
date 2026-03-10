from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "merge_metadata.py"
    spec = importlib.util.spec_from_file_location("merge_metadata", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


merge_metadata = _load_module()
REPO_ROOT = Path(__file__).resolve().parents[1]
SHAPE_YAML = REPO_ROOT / "SHAPE" / "rnastruct00001.yaml"


def test_extract_run_metadata_map_includes_sample_fields():
    metadata = {
        "raw_data": {
            "run_accessions": [
                {
                    "accession": "GSM1",
                    "sample_name": "HeLa_treated_r1",
                    "cell_line": "HeLa",
                    "condition": "treated",
                    "replicate": 1,
                }
            ]
        }
    }

    result = merge_metadata.extract_run_metadata_map(metadata)

    assert result == {
        "GSM1": {
            "sample_name": "HeLa_treated_r1",
            "cell_line": "HeLa",
            "condition": "treated",
            "replicate": "1",
        }
    }


def test_main_writes_new_sample_metadata_columns(tmp_path, monkeypatch, capsys):
    samplesheet_path = tmp_path / "fetchngs.csv"
    output_path = tmp_path / "merged.csv"

    samplesheet_path.write_text(
        (
            "sample_alias,fastq_1,fastq_2\n"
            "GSM4333255,s1_R1.fastq.gz,s1_R2.fastq.gz\n"
            "GSM4333259,s2_R1.fastq.gz,s2_R2.fastq.gz\n"
            "GSMX,sx_R1.fastq.gz,sx_R2.fastq.gz\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "merge_metadata.py",
            "--samplesheet",
            str(samplesheet_path),
            "--metadata",
            str(SHAPE_YAML),
            "--out",
            str(output_path),
        ],
    )

    rc = merge_metadata.main()
    assert rc == 0

    header = output_path.read_text(encoding="utf-8").splitlines()[0]
    assert header == (
        "sample,sample_id,fastq_1,fastq_2,method,principle,"
        "cell_line,condition,replicate,organism,adapter_3p,adapter_5p,umi_pattern"
    )

    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert rows[0]["sample"] == "HEK293T_untreated_r1"
    assert rows[0]["cell_line"] == "HEK293T"
    assert rows[0]["condition"] == "untreated"
    assert rows[0]["replicate"] == "1"
    assert rows[0]["organism"] == "Homo sapiens"
    assert rows[1]["sample"] == "K562_untreated_r1"
    assert rows[1]["cell_line"] == "K562"
    assert rows[1]["condition"] == "untreated"
    assert rows[1]["replicate"] == "1"
    assert rows[1]["method"] == "SHAPE"

    out = capsys.readouterr().out
    assert f"Wrote 2 rows to {output_path}" in out
