#!/usr/bin/env python3
import argparse
import sys

try:
    import yaml
except Exception as exc:
    sys.stderr.write(
        "Missing dependency: pyyaml is required. Install with `pip install pyyaml`.\n"
    )
    raise


def _run_accessions_from_list(value):
    return [str(item["accession"]).strip() for item in value]


def extract_ids(data):
    run_accessions = _run_accessions_from_list(data["raw_data"]["run_accessions"])
    return run_accessions, "run_accessions"


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract IDs from a YAML file and write to a single-column CSV file. "
            "Use raw_data.run_accessions[].accession values only."
        )
    )
    parser.add_argument("yaml_path", help="Path to input YAML file")
    parser.add_argument("output_csv", help="Path to output CSV file")
    args = parser.parse_args()

    with open(args.yaml_path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    result = extract_ids(data)
    ids, source = result

    with open(args.output_csv, "w", encoding="utf-8") as handle:
        handle.write("\n".join(ids))
        handle.write("\n")
    sys.stderr.write(f"Wrote {len(ids)} IDs from {source}.\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
