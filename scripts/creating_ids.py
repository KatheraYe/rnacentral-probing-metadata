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


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x is not None and str(x).strip()]
    text = str(value).strip()
    return [text] if text else []


def extract_ids(data):
    if isinstance(data, dict):
        run_accessions = _as_list(data.get("run_accessions"))
        if run_accessions:
            return run_accessions, "run_accessions"

        accession = _as_list(data.get("accession"))
        if accession:
            return accession, "accession"

        for value in data.values():
            result = extract_ids(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = extract_ids(item)
            if result:
                return result
    return None


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract IDs from a YAML file and write to a single-column CSV file. "
            "Prefer run_accessions (subset mode), else use accession (full mode)."
        )
    )
    parser.add_argument("yaml_path", help="Path to input YAML file")
    parser.add_argument("output_csv", help="Path to output CSV file")
    args = parser.parse_args()

    with open(args.yaml_path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    result = extract_ids(data)
    if not result:
        sys.stderr.write("No run_accessions or accession found in YAML.\n")
        return 1
    ids, source = result

    with open(args.output_csv, "w", encoding="utf-8") as handle:
        handle.write("\n".join(ids))
        handle.write("\n")
    sys.stderr.write(f"Wrote {len(ids)} IDs from {source}.\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
