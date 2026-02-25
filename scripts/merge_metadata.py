#!/usr/bin/env python3
"""Build a pipeline samplesheet from fetchngs CSV + dataset YAML.

Output format:
sample,sample_id,fastq_1,fastq_2,method,principle,cell_line,condition,replicate,genome_build,adapter_3p,adapter_5p,umi_pattern
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for metadata merge inputs and output path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samplesheet", required=True, help="Path to fetchngs samplesheet CSV")
    parser.add_argument("--metadata", required=True, help="Path to manual dataset metadata YAML")
    parser.add_argument(
        "--out",
        help="Output samplesheet CSV path. Default: <dataset_id>_samplesheet.csv",
    )
    return parser.parse_args()


def read_yaml(path: Path) -> dict:
    """Load metadata YAML and ensure the top-level object is a mapping."""
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Metadata YAML must be a mapping: {path}")
    return data


def extract_run_metadata_map(metadata: dict) -> dict[str, dict[str, str]]:
    """Map raw-data accession IDs to per-sample metadata from manual YAML."""
    return {
        str(item["accession"]).strip(): {
            "sample_name": str(item["sample_name"]).strip(),
            "cell_line": str(item.get("cell_line", "")).strip(),
            "condition": str(item.get("condition", "")).strip(),
            "replicate": str(item.get("replicate", "")).strip(),
        }
        for item in metadata["raw_data"]["run_accessions"]
    }


def normalize_method(method: str) -> str:
    """Normalize method labels to SHAPE or DMS based on substring matching."""
    value = method.strip().upper()
    if "SHAPE" in value:
        return "SHAPE"
    if "DMS" in value:
        return "DMS"
    raise ValueError(f"Unsupported method '{method}'. Expected a SHAPE- or DMS-based method.")


def main() -> int:
    """Merge fetchngs samplesheet rows with dataset metadata and write output CSV."""
    args = parse_args()
    samplesheet_path = Path(args.samplesheet)
    metadata_path = Path(args.metadata)
    out_path: Path | None = Path(args.out) if args.out else None

    with samplesheet_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Empty samplesheet: {samplesheet_path}")

    metadata = read_yaml(metadata_path)
    run_metadata_map = extract_run_metadata_map(metadata)
    dataset_id = metadata.get("dataset_id", "")
    experiment = (metadata.get("experiment") or metadata.get("data_type") or {})
    method = normalize_method((experiment.get("method", "")))
    if out_path is None:
        if dataset_id:
            out_path = metadata_path.parent / f"{dataset_id}_samplesheet.csv"
        else:
            out_path = metadata_path.parent / "merged_samplesheet.csv"

    out_rows = []
    missing_given_name = 0
    for row in rows:
        run_accession = (row.get("sample_alias") or "").strip()
        run_metadata = run_metadata_map.get(run_accession)
        if not run_metadata:
            missing_given_name += 1
            continue

        out_rows.append(
            {
                "sample": run_metadata["sample_name"],
                "sample_id": run_accession,
                "cell_line": run_metadata["cell_line"],
                "condition": run_metadata["condition"],
                "replicate": run_metadata["replicate"],
                "fastq_1": row.get("fastq_1", ""),
                "fastq_2": row.get("fastq_2", ""),
                "method": method,
                "principle": experiment.get("principle", ""),
                "genome_build": (metadata.get("organism") or {}).get("genome_build", ""),
                "adapter_3p": experiment.get("adapter_3p", ""),
                "adapter_5p": experiment.get("adapter_5p", ""),
                "umi_pattern": experiment.get("umi_pattern", ""),
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
        "method",
        "principle",
        "cell_line",
        "condition",
        "replicate",
        "genome_build",
        "adapter_3p",
        "adapter_5p",
        "umi_pattern",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
