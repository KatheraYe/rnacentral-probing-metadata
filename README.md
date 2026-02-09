# rnacentral-probing-metadata
Metadata for structural chemical probing experiments for RNAcentral


This repository stores metadata YAML files for chemical probing datasets (for example in `SHAPE/` and `DMS/`), validates them, extracts accessions into ID text files, and uses those IDs to download FASTQ files with `nf-core/fetchngs` on Slurm. 

The yaml file must follow the schema provided (see example rnastruct00001.yaml), and if multiple organisms are used in the same dataset, you must create a seperate yaml file per organism (e.g. one for human and another for mouse).
You can provide either the full dataset in `accession` or a subset of the previous in `run_accessions` (which is optional).
The `accession` can be any of the identifiers supported in `nf-core/fetchngs` such as SRA, ENA, DDBJ, GEO. Full list can be found here: https://nf-co.re/fetchngs/1.12.0/docs/usage 