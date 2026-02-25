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
    metadata_path = tmp_path / "metadata.yaml"
    output_path = tmp_path / "merged.csv"

    samplesheet_path.write_text(
        (
            "sample_alias,fastq_1,fastq_2\n"
            "GSM1,s1_R1.fastq.gz,s1_R2.fastq.gz\n"
            "GSM2,s2_R1.fastq.gz,s2_R2.fastq.gz\n"
            "GSMX,sx_R1.fastq.gz,sx_R2.fastq.gz\n"
        ),
        encoding="utf-8",
    )
    metadata_path.write_text(
        (
            "dataset_id: rnastruct99999\n"
            "organism:\n"
            "  name: Homo sapiens\n"
            "  genome_build: hg38\n"
            "experiment:\n"
            "  method: icSHAPE\n"
            "  principle: RT-stop\n"
            "raw_data:\n"
            "  repository: GEO\n"
            "  accession: GSE1\n"
            "  run_accessions:\n"
            "    - accession: GSM1\n"
            "      sample_name: HeLa_treated_r1\n"
            "      cell_line: HeLa\n"
            "      condition: treated\n"
            "      replicate: 1\n"
            "    - accession: GSM2\n"
            "      sample_name: K562_untreated_r1\n"
            "      cell_line: K562\n"
            "      condition: untreated\n"
            "      replicate: 1\n"
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
            str(metadata_path),
            "--out",
            str(output_path),
        ],
    )

    rc = merge_metadata.main()
    assert rc == 0

    header = output_path.read_text(encoding="utf-8").splitlines()[0]
    assert header == (
        "sample,sample_id,fastq_1,fastq_2,method,principle,"
        "cell_line,condition,replicate,genome_build,adapter_3p,adapter_5p,umi_pattern"
    )

    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert rows[0]["sample"] == "HeLa_treated_r1"
    assert rows[0]["cell_line"] == "HeLa"
    assert rows[0]["condition"] == "treated"
    assert rows[0]["replicate"] == "1"
    assert rows[1]["sample"] == "K562_untreated_r1"
    assert rows[1]["cell_line"] == "K562"
    assert rows[1]["condition"] == "untreated"
    assert rows[1]["replicate"] == "1"
    assert rows[1]["method"] == "SHAPE"

    out = capsys.readouterr().out
    assert f"Wrote 2 rows to {output_path}" in out
