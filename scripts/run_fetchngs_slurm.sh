#!/usr/bin/env bash
#SBATCH --job-name=fetchngs
#SBATCH --output=logs/fetchngs_%j.out
#SBATCH --error=logs/fetchngs_%j.err
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --partition=YOUR_PARTITION
#SBATCH --account=YOUR_ACCOUNT

set -euo pipefail

module load nextflow

REPO_DIR="/path/to/rnacentral-probing-metadata"
IDS_FILE="${REPO_DIR}/ids/SHAPE_rnastruct00001.txt"
OUTDIR="${REPO_DIR}/fastq"
WORKDIR="${REPO_DIR}/work"

mkdir -p "${REPO_DIR}/logs" "${OUTDIR}" "${WORKDIR}"

cd "${REPO_DIR}"

nextflow run nf-core/fetchngs -r 1.12.0 \
  --input "${IDS_FILE}" \
  --outdir "${OUTDIR}" \
  -resume
