#!/usr/bin/env bash
set -euo pipefail

schema="schema/rnastruct.schema.yaml"

if ! command -v linkml-validate >/dev/null 2>&1; then
  echo "linkml-validate not found. Install with: pip install linkml" >&2
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "python not found in PATH." >&2
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

mkdir -p ids

for yaml in "${yamls[@]}"; do
  if [ ! -s "${yaml}" ]; then
    echo "Skipping empty YAML ${yaml}"
    continue
  fi
  echo "Validating ${yaml}"
  linkml-validate --schema "${schema}" "${yaml}"

  base="$(basename "${yaml}" .yaml)"
  dir="$(basename "$(dirname "${yaml}")")"
  out="ids/${dir}_${base}.txt"
  echo "Generating ${out}"
  python scripts/creating_ids.py "${yaml}" "${out}"
done
