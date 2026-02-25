# rnacentral-probing-metadata

Metadata for structural chemical probing experiments for RNAcentral.

This repository stores metadata YAML files for chemical probing datasets (for example in `SHAPE/` and `DMS/`) that are validated with LinkML via GitHub Actions. Once a YAML file is accepted, the pipeline downloads FASTQ files using `nf-core/fetchngs` and creates a final `samplesheet.csv` that can be used as input for `nf-core/rnastructurome`.

Each YAML file must follow the provided schema (see example `rnastruct00001.yaml`). If multiple organisms are used in the same dataset, create a separate YAML file per organism (for example, one for human and one for mouse).

For raw data download, provide an `accession` supported by `nf-core/fetchngs` (for example SRA, ENA, DDBJ, GEO). The full list is available here: https://nf-co.re/fetchngs/1.12.0/docs/usage

To reliably track sample metadata, include the individual `run_accession` for each sample and a biologically meaningful sample name (for example `<cell_line>_<condition>_<replicate>`).

## Metadata schema checks

The validator (`linkml-validate` against `schema/rnastruct.schema.yaml`) makes sure the minimim requiered fields for running the pipeline end-to-end are present. 
The requiered fields are: 
- dataset_id, which has to follow the `rnastruct00001.yaml` naming convention and must be unique (ideally +1 of the last one present in this repo).
- organims name (e.g. Homo sapiens) and genome build (e.g. hg38)
- publication (doi)
- raw_data: repository (e.g. GEO), accession (global accession for that dataset) and run_accession (this has to have the individual sample accession, a sample_name, which is custom but should be descriptive, cell_line, condition (`untreated, treated or denatured`) and replicate).

All other fields are optional and if not known can just be null.

