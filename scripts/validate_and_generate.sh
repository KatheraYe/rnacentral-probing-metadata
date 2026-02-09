#!/usr/bin/env bash
set -euo pipefail

schema="schema/rnastruct.schema.yaml"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${repo_dir}/../ids"

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
  if [ ! -s "${yaml}" ]; then
    echo "Skipping empty YAML ${yaml}"
    continue
  fi
  base="$(basename "${yaml}" .yaml)"
  dir="$(basename "$(dirname "${yaml}")")"
  output="${output_dir}/${dir}_${base}.txt"

  if [ -s "${output}" ] && [ "${output}" -nt "${yaml}" ]; then
    continue
  fi

  echo "Validating ${yaml}"
  linkml-validate --schema "${schema}" "${yaml}"

  echo "Generating ${output}"
  python3 scripts/creating_ids.py "${yaml}" "${output}"
done
