# RNAcentral chemical probing metadata

Metadata for structural chemical probing experiments for RNAcentral.

This repository stores metadata YAML files for chemical probing datasets (for example in `SHAPE/` and `DMS/`) that are validated with [LinkML](https://linkml.io) via GitHub Actions. Once a YAML file is accepted, the pipeline downloads FASTQ files using `nf-core/fetchngs` and creates a final `samplesheet.csv` that can be used as input for `nf-core/rnastructurome`.

## Adding a new metadata YAML via pull request

To add a new dataset to this repository:

1. Clone this repository to your local machine.
2. Create a new branch from master with a descriptive name including “Add” (e.g. Add-new-shape-dataset).
3. Create a new YAML file (see section below) in the appropriate directory (for example `SHAPE/` or `DMS/`) and populate it according to the schema requirements.
4. Open a pull request with that new YAML file.
5. Wait for the GitHub Actions checks to validate the YAML.
6. If the checks pass, someone from RNAcentral will review and merge the pull request.
7. If the checks fail, inspect the GitHub Actions logs, fix the reported issue in the YAML, and update the pull request.

## Creating a new YAML file

1. Start from the template: use the example file (rnastruct00001.yaml) as a guide. Your YAML should follow the same structure. If your dataset includes multiple organisms, create one YAML file per organism (e.g. one for Homo sapiens, one for Mus musculus).

2. Choose a dataset id that is a consecutive number from the last one in the repo (e.g. rnastruct00010). Check both DMS/ and SHAPE/ to find the latest id number.

3. You must also include the organism in Latin name (e.g. Homo sapiens), the method (which can be SHAPE or DMS variants) and principal (RT-stop or MaP) of this experiement, a publication DOI, and fill out the raw_data section.

4. Each sample listed under run_accessions should include a biologically meaningful and distinguishable sample_name, along with cell_line (no white spaces), condition (one of untreated, treated, or denatured), and replicate (just a number). The sample accession id must be supported by nf-core/fetchngs (e.g. SRA, ENA, DDBJ, GEO; [see the fetchngs documentation for the full list](https://nf-co.re/fetchngs/1.12.0/docs/usage)).

5. If including an OBI id, use a valid term from the [Ontology for Biomedical Investigations](http://obi-ontology.org/) / [obi-ontology/obi](https://github.com/obi-ontology/obi). If the experimental context is provided, it must be one of in_vivo, in_vitro, or denatured.

6. All other fields are optional and can be set to null if not available.

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
- `dataset_id`, which must match the `rnastruct00001` naming convention
- `organism` in Latin name format
- `experiment.method`, which must contain `SHAPE` or `DMS`
- `experiment.principle`, which must be `RT-stop` or `MaP`
- `publication.doi`
- `raw_data.repository`, which must be one of `SRA`, `ENA`, `GEO`, or `DDBJ`
- `raw_data.accession`
- `raw_data.run_accessions`, where each item must include `accession`, `sample_name`, `cell_line`, `condition`, and `replicate`

All other fields are optional and, if not known, can be `null`.
The optional field `experiment.context`, when provided, must use one or more of: `in_vivo`, `in_vitro`, or `denatured`.
