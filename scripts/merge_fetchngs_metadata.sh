#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <repo_dir> <outdir>" >&2
  exit 1
fi

repo_dir="$1"
outdir="$2"

merged_dir="${outdir}/samplesheet"
mkdir -p "${merged_dir}"

shopt -s nullglob
for yaml in "${repo_dir}"/SHAPE/*.yaml "${repo_dir}"/DMS/*.yaml; do
  [ -s "${yaml}" ] || continue

  dataset_id="$(basename "${yaml}" .yaml)"
  samplesheet_csv="${outdir}/${dataset_id}/samplesheet/samplesheet.csv"

  if [ ! -s "${samplesheet_csv}" ]; then
    alt_match="$(find "${outdir}" -type f -name samplesheet.csv | grep "/${dataset_id}/" | head -n 1 || true)"
    if [ -n "${alt_match}" ]; then
      samplesheet_csv="${alt_match}"
    else
      echo "ERROR: samplesheet.csv not found for ${dataset_id}. Expected ${samplesheet_csv}" >&2
      exit 1
    fi
  fi

  out_csv="${merged_dir}/${dataset_id}_samplesheet.csv"

  python3 "${repo_dir}/scripts/merge_metadata.py" \
    --samplesheet "${samplesheet_csv}" \
    --metadata "${yaml}" \
    --out "${out_csv}"
done

manifest="${merged_dir}/rnastruct_samplesheets_manifest.txt"
find "${merged_dir}" -maxdepth 1 -type f -name '*_samplesheet.csv' | sort > "${manifest}"

if [ ! -s "${manifest}" ]; then
  echo "ERROR: no merged rnastruct samplesheets were generated in ${merged_dir}" >&2
  exit 1
fi
