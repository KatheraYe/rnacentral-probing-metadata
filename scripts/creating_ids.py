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


def extract_run_accessions(data):
    if isinstance(data, dict):
        if "run_accessions" in data and isinstance(data["run_accessions"], list):
            return [str(x) for x in data["run_accessions"]]
        for value in data.values():
            result = extract_run_accessions(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = extract_run_accessions(item)
            if result:
                return result
    return []


def main():
    parser = argparse.ArgumentParser(
        description="Extract run_accessions from a YAML file and write to a txt file."
    )
    parser.add_argument("yaml_path", help="Path to input YAML file")
    parser.add_argument("output_txt", help="Path to output txt file")
    args = parser.parse_args()

    with open(args.yaml_path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    run_accessions = extract_run_accessions(data)
    if not run_accessions:
        sys.stderr.write("No run_accessions found in YAML.\n")
        return 1

    with open(args.output_txt, "w", encoding="utf-8") as handle:
        handle.write("\n".join(run_accessions))
        handle.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
