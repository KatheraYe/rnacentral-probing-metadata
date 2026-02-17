#!/usr/bin/env python3
"""Build a pipeline samplesheet from fetchngs CSV + dataset YAML.

Output format:
sample,sample_id,fastq_1,fastq_2,library_layout,method,principle,organism
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samplesheet", required=True, help="Path to fetchngs samplesheet CSV")
    parser.add_argument("--metadata", required=True, help="Path to manual dataset metadata YAML")
    parser.add_argument(
        "--out",
        help="Output samplesheet CSV path. Default: <dataset_id>_samplesheet.csv",
    )
    return parser.parse_args()


def read_yaml(path: Path) -> dict:
    with path.open() as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Metadata YAML must be a mapping: {path}")
    return data


def extract_run_name_map(metadata: dict) -> dict[str, str]:
    return {
        str(item["accession"]).strip(): str(item["sample_name"]).strip()
        for item in metadata["raw_data"]["run_accessions"]
    }


def resolve_name_for_row(row: dict, run_name_map: dict[str, str]) -> str:
    lookup_keys = (
        (row.get("run_accession") or "").strip(),
        (row.get("sample_alias") or "").strip(),
        (row.get("sample_accession") or "").strip(),
        (row.get("experiment_accession") or "").strip(),
        (row.get("study_accession") or "").strip(),
        (row.get("study_alias") or "").strip(),
    )
    for key in lookup_keys:
        if key and key in run_name_map:
            return run_name_map[key]
    return ""


def main() -> int:
    args = parse_args()
    samplesheet_path = Path(args.samplesheet)
    metadata_path = Path(args.metadata)
    out_path: Path | None = Path(args.out) if args.out else None

    with samplesheet_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Empty samplesheet: {samplesheet_path}")

    metadata = read_yaml(metadata_path)
    run_name_map = extract_run_name_map(metadata)
    dataset_id = metadata.get("dataset_id", "")
    if out_path is None:
        if dataset_id:
            out_path = metadata_path.parent / f"{dataset_id}_samplesheet.csv"
        else:
            out_path = metadata_path.parent / "merged_samplesheet.csv"

    out_rows = []
    missing_given_name = 0
    for row in rows:
        run_accession = (row.get("run_accession") or "").strip()
        given_name = resolve_name_for_row(row, run_name_map)
        if not given_name:
            missing_given_name += 1
            continue

        out_rows.append(
            {
                "sample": given_name,
                "sample_id": run_accession,
                "fastq_1": row.get("fastq_1", ""),
                "fastq_2": row.get("fastq_2", ""),
                "library_layout": row.get("library_layout", ""),
                "method": (metadata.get("data_type") or {}).get("method", ""),
                "principle": (metadata.get("data_type") or {}).get("principle", ""),
                "organism": (metadata.get("organism") or {}).get("name", ""),
            }
        )

    if not out_rows:
        raise ValueError("No rows produced. Check run_accessions accessions and fetchngs IDs.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample",
        "sample_id",
        "fastq_1",
        "fastq_2",
        "library_layout",
        "method",
        "principle",
        "organism",
    ]
    with out_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    if missing_given_name:
        raise ValueError(
            f"Could not resolve given_name from run_accessions for {missing_given_name} rows."
        )

    print(f"Wrote {len(out_rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
