# rnacentral-probing-metadata
Metadata for structural chemical probing experiments for RNAcentral


This repository stores metadata YAML files for chemical probing datasets (for example in `SHAPE/` and `DMS/`) which have been validated via linkML with github actions. Once the YAML file is accepted, this pipeline downloads the fastq files using nf-core/fetchngs, and creates a final samplesheet.csv that can be used as input for nf-core/rnastructurome.

The yaml file must follow the schema provided (see example rnastruct00001.yaml), and if multiple organisms are used in the same dataset, you must create a seperate yaml file per organism (e.g. one for human and another for mouse).
For downloading the raw data, you should provide an `accession` which can be any of the identifiers supported in `nf-core/fetchngs` such as SRA, ENA, DDBJ, GEO. Full list can be found here: https://nf-co.re/fetchngs/1.12.0/docs/usage 
In order to reliably keep track of the sample metadata, you need to add the individual run_accession for each sample and a biologically meaningfull sample name (e.g. <cell_line>_<condition>_<replicate>)

## Metadata schema checks

The validator (`linkml-validate` against `schema/rnastruct.schema.yaml`) currently enforces:

- `dataset_id` must match: `rnastruct<digits>` (for example `rnastruct00001`).
- `organism.name` must be a scientific name (for example `Homo sapiens`).
- `data_type.method` must contain either `SHAPE` or `DMS`.
- `data_type.principle` must be one of: `RT-stop`, `MaP`.
- `data_type.context` must be a list with one or more of: `in_vivo`, `in_vitro`, `ex_vivo`.
- `publication.doi` must match DOI format.
- `raw_data.repository` must be one of: `SRA`, `ENA`, `GEO`, `DDBJ`.
- `raw_data.accession` must match supported accession patterns (SRA/ENA/DDBJ/GEO-style IDs).
- `raw_data.run_accessions` must be a list of objects with required fields: `accession` and `sample_name`.
