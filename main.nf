nextflow.enable.dsl = 2

params.repo_dir = "/hps/nobackup/agb/rnacentral/chemicalprob/rnacentral-probing-metadata"
params.ids_dir = "/hps/nobackup/agb/rnacentral/chemicalprob/ids"
params.outdir = "/hps/nobackup/agb/rnacentral/chemicalprob/FASTQ"
params.fetchngs_revision = "1.12.0"
params.fetchngs_profile = "slurm"
params.nxf_singularity_cachedir = "/hps/nobackup/agb/rnacentral/chemicalprob/.singularity_cache"

process VALIDATE_AND_GENERATE {
  tag "validate-and-generate"
  executor "local"

  input:
  val repo_dir
  val ids_dir
  path yaml_files

  output:
  path "ids_manifest.txt", emit: ids_manifest

  script:
  """
  set -euo pipefail

  mkdir -p "${ids_dir}"

  (
    cd "${repo_dir}"
    IDS_DIR="${ids_dir}" bash scripts/validate_and_generate.sh
  )

  find "${ids_dir}" -maxdepth 1 -type f -name '*.csv' | sort > ids_manifest.txt

  if [ ! -s ids_manifest.txt ]; then
    echo "ERROR: no CSV files were generated in ${ids_dir}" >&2
    exit 1
  fi
  """
}

process RUN_FETCHNGS {
  tag "run-fetchngs"
  executor "local"

  input:
  path ids_manifest
  val repo_dir
  val outdir
  val fetchngs_revision
  val fetchngs_profile
  val nxf_singularity_cachedir

  output:
  path "fetchngs.done"

  script:
  """
  set -euo pipefail

  mkdir -p "${outdir}"
  export NXF_SINGULARITY_CACHEDIR="${nxf_singularity_cachedir}"

  while IFS= read -r ids_file; do
    [ -n "\${ids_file}" ] || continue

    sample_name="\$(basename "\${ids_file}" .csv)"
    sample_outdir="${outdir}/\${sample_name}"
    done_file="\${sample_outdir}/.fetchngs.done"

    if [ -f "\${done_file}" ] && [ "\${done_file}" -nt "\${ids_file}" ]; then
      echo "Skipping \${ids_file}; output is up to date."
      continue
    fi

    mkdir -p "\${sample_outdir}"

    nextflow run nf-core/fetchngs -r "${fetchngs_revision}" \
      -c "${repo_dir}/nextflow.config" \
      -profile "${fetchngs_profile}" \
      --input "\${ids_file}" \
      --outdir "\${sample_outdir}" \
      -resume

    touch "\${done_file}"
  done < "${ids_manifest}"

  touch fetchngs.done
  """
}

process MERGE_FETCHNGS_METADATA {
  tag "merge-fetchngs-metadata"
  executor "local"

  input:
  path fetch_done
  val repo_dir
  val outdir
  path yaml_files

  output:
  path "rnastruct_samplesheets_manifest.txt", emit: rnastruct_manifest

  script:
  """
  set -euo pipefail

  merged_dir="${outdir}/samplesheet"
  mkdir -p "\${merged_dir}"

  shopt -s nullglob
  for yaml in "${repo_dir}"/SHAPE/*.yaml "${repo_dir}"/DMS/*.yaml; do
    [ -s "\${yaml}" ] || continue

    dataset_id="\$(basename "\${yaml}" .yaml)"
    samplesheet_csv="${outdir}/\${dataset_id}/samplesheet/samplesheet.csv"

    if [ ! -s "\${samplesheet_csv}" ]; then
      alt_match="\$(find "${outdir}" -type f -name samplesheet.csv | grep "/\${dataset_id}/" | head -n 1 || true)"
      if [ -n "\${alt_match}" ]; then
        samplesheet_csv="\${alt_match}"
      else
        echo "ERROR: samplesheet.csv not found for \${dataset_id}. Expected \${samplesheet_csv}" >&2
        exit 1
      fi
    fi

    out_csv="\${merged_dir}/\${dataset_id}_samplesheet.csv"

    if [ -s "\${out_csv}" ] && [ "\${out_csv}" -nt "\${samplesheet_csv}" ] && [ "\${out_csv}" -nt "\${yaml}" ]; then
      echo "Skipping merge for \${dataset_id}; output is up to date."
      continue
    fi

    python3 "${repo_dir}/scripts/merge_metadata.py" \
      --samplesheet "\${samplesheet_csv}" \
      --metadata "\${yaml}" \
      --out "\${out_csv}"
  done

  find "\${merged_dir}" -maxdepth 1 -type f -name '*_samplesheet.csv' | sort > rnastruct_samplesheets_manifest.txt

  if [ ! -s rnastruct_samplesheets_manifest.txt ]; then
    echo "ERROR: no merged rnastruct samplesheets were generated in \${merged_dir}" >&2
    exit 1
  fi
  """
}

workflow {
  yaml_files = Channel
    .fromPath("${params.repo_dir}/{SHAPE,DMS}/*.yaml")
    .ifEmpty { error "No YAML files found under ${params.repo_dir}/SHAPE or ${params.repo_dir}/DMS" }
    .collect()
  validate = VALIDATE_AND_GENERATE(params.repo_dir, params.ids_dir, yaml_files)
  fetch = RUN_FETCHNGS(
    validate.ids_manifest,
    params.repo_dir,
    params.outdir,
    params.fetchngs_revision,
    params.fetchngs_profile,
    params.nxf_singularity_cachedir
  )
  MERGE_FETCHNGS_METADATA(
    fetch,
    params.repo_dir,
    params.outdir,
    yaml_files
  )
}
