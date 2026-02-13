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

  find "${ids_dir}" -maxdepth 1 -type f -name '*.csv' | sort > "${PWD}/ids_manifest.txt"

  if [ ! -s "${PWD}/ids_manifest.txt" ]; then
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

workflow {
  validate = VALIDATE_AND_GENERATE(params.repo_dir, params.ids_dir)
  RUN_FETCHNGS(
    validate.ids_manifest,
    params.repo_dir,
    params.outdir,
    params.fetchngs_revision,
    params.fetchngs_profile,
    params.nxf_singularity_cachedir
  )
}
