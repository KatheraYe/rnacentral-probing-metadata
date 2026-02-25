#!/usr/bin/env python3
"""Validate uniqueness of dataset and run accession IDs across metadata YAML files."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import yaml


def collect_metadata_files(root: Path, directories: list[str]) -> list[Path]:
    """Collect metadata YAML files from the configured directories."""
    files: list[Path] = []
    for directory in directories:
        base = root / directory
        files.extend(sorted(base.glob("*.yaml")))
        files.extend(sorted(base.glob("*.yml")))
    return sorted(set(files))


def find_uniqueness_issues(paths: list[Path]) -> list[str]:
    """Return uniqueness issues for dataset_id and run_accessions IDs."""
    issues: list[str] = []
    dataset_ids: dict[str, list[str]] = defaultdict(list)
    run_accessions: dict[str, list[str]] = defaultdict(list)

    for path in paths:
        try:
            with path.open(encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except Exception as exc:  # pragma: no cover
            issues.append(f"{path}: failed to parse YAML ({exc})")
            continue

        if not isinstance(data, dict):
            issues.append(f"{path}: top-level YAML must be a mapping")
            continue

        dataset_id = str(data.get("dataset_id", "")).strip()
        if not dataset_id:
            issues.append(f"{path}: missing dataset_id")
        else:
            dataset_ids[dataset_id].append(str(path))

        raw_data = data.get("raw_data")
        if not isinstance(raw_data, dict):
            issues.append(f"{path}: missing or invalid raw_data")
            continue

        runs = raw_data.get("run_accessions")
        if not isinstance(runs, list):
            issues.append(f"{path}: missing or invalid raw_data.run_accessions")
            continue

        for index, run in enumerate(runs, start=1):
            if not isinstance(run, dict):
                issues.append(f"{path}: run_accessions item {index} is not a mapping")
                continue
            accession = str(run.get("accession", "")).strip()
            if not accession:
                issues.append(f"{path}: run_accessions item {index} missing accession")
                continue
            run_accessions[accession].append(f"{path} (item {index})")

    for dataset_id, locations in sorted(dataset_ids.items()):
        if len(locations) > 1:
            issues.append(
                f"Duplicate dataset_id '{dataset_id}' found in: {', '.join(locations)}"
            )

    for accession, locations in sorted(run_accessions.items()):
        if len(locations) > 1:
            issues.append(
                f"Duplicate run accession '{accession}' found in: {', '.join(locations)}"
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root containing metadata directories (default: current directory).",
    )
    parser.add_argument(
        "--dirs",
        nargs="+",
        default=["SHAPE", "DMS"],
        help="Metadata directories to scan (default: SHAPE DMS).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    files = collect_metadata_files(root, args.dirs)

    if not files:
        print("No metadata YAML files found to validate.")
        return 0

    issues = find_uniqueness_issues(files)
    if issues:
        print("Uniqueness validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"Uniqueness validation passed for {len(files)} metadata file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
