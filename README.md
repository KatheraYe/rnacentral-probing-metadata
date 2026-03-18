# rnacentral-probing-metadata

Metadata for structural chemical probing experiments for RNAcentral.

This repository stores metadata YAML files for chemical probing datasets (for example in `SHAPE/` and `DMS/`) that are validated with [LinkML](https://linkml.io) via GitHub Actions. Once a YAML file is accepted, the pipeline downloads FASTQ files using `nf-core/fetchngs` and creates a final `samplesheet.csv` that can be used as input for `nf-core/rnastructurome`.

Each YAML file must follow the provided schema (see example `rnastruct00001.yaml`). If multiple organisms are used in the same dataset, create a separate YAML file per organism (for example, one for human and one for mouse).

For raw data download, provide an `accession` supported by `nf-core/fetchngs` (for example SRA, ENA, DDBJ, GEO). The full list is available here: https://nf-co.re/fetchngs/1.12.0/docs/usage

To reliably track sample metadata, include the individual `run_accession` for each sample and a biologically meaningful sample name (for example `<cell_line>_<condition>_<replicate>`).

If you provide `experiment.obi` in a YAML file, use an OBI term from the [Ontology for Biomedical Investigations](http://obi-ontology.org/) / [obi-ontology/obi](https://github.com/obi-ontology/obi).

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) then run:

```bash
uv sync --dev
```

To run the tests:

```bash
uv run pytest
```

## Metadata schema checks

The validator (`linkml-validate` against `schema/rnastruct.schema.yaml`) makes sure the minimum required fields for running the pipeline end-to-end are present. 
The required fields are: 
- dataset_id, which has to follow the `rnastruct00001.yaml` naming convention and must be unique (ideally +1 of the last one present in this repo).
- organism in Latin name format (e.g. Homo sapiens)
- publication (doi)
- raw_data: repository (e.g. GEO), accession (global accession for that dataset) and run_accession (this has to have the individual sample accession, a sample_name, which is custom but should be descriptive, cell_line, condition (`untreated, treated or denatured`) and replicate).

All other fields are optional and if not known can just be null.
The optional field experiment.context, when provided, must use the schema enum values: `in_vivo`, `in_vitro`, or `denatured`.
