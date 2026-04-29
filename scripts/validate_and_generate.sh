#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_dir}"

schema="schema/rnastruct.schema.yaml"
# Allow callers (e.g. Slurm wrapper) to override where ID CSVs are written.
output_dir="${IDS_DIR:-${repo_dir}/ids}"

if ! command -v linkml-validate >/dev/null 2>&1; then
  echo "linkml-validate not found. Install with: pip install linkml" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found in PATH." >&2
  exit 1
fi

shopt -s nullglob
shape_yamls=(SHAPE/*.yaml)
dms_yamls=(DMS/*.yaml)
yamls=("${shape_yamls[@]}" "${dms_yamls[@]}")

if [ ${#yamls[@]} -eq 0 ]; then
  echo "No YAML files found under SHAPE/ or DMS/." >&2
  exit 1
fi

mkdir -p "${output_dir}"

for yaml in "${yamls[@]}"; do
  base="$(basename "${yaml}" .yaml)"
  output="${output_dir}/${base}.csv"

  echo "Validating ${yaml}"
  linkml-validate --schema "${schema}" "${yaml}"

  echo "Validating OBI ID for ${yaml}"
  python3 scripts/validate_obi_ids.py "${yaml}"

  echo "Generating ${output}"
  python3 scripts/creating_ids.py "${yaml}" "${output}"
done
