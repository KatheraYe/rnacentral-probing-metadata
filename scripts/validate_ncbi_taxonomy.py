#!/usr/bin/env python3
"""Validate viral organism + strain metadata against NCBI Taxonomy."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml


VIRAL_ORGANISMS = {
    "Influenza A virus",
    "SARS-CoV-2",
    "Zika virus",
    "HIV",
    "Rotavirus A",
}

NCBI_ORGANISM_ALIASES = {
    "SARS-CoV-2": "Severe acute respiratory syndrome coronavirus 2",
    "HIV": "Human immunodeficiency virus 1",
}

# NCBI Taxonomy does not consistently model these isolate/strain names as
# separate taxonomy names. Still require strain metadata, but validate the
# species-level taxon when exact strain candidates do not resolve.
SPECIES_LEVEL_TAXONOMY_ORGANISMS = {
    "SARS-CoV-2",
}

NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_REQUEST_DELAY_SECONDS = 0.34


def base_taxonomy_names(organism: str) -> list[str]:
    """Return exact NCBI Taxonomy names for the organism itself."""
    bases = [organism]
    alias = NCBI_ORGANISM_ALIASES.get(organism)
    if alias and alias not in bases:
        bases.append(alias)
    return bases


def candidate_taxonomy_names(organism: str, strain: str) -> list[str]:
    """Return exact NCBI Taxonomy names to try for organism + strain."""
    strain = strain.strip()
    if organism == "Influenza A virus":
        return [f"{organism} ({strain})"]
    if organism == "Rotavirus A":
        return [
            f"Bovine rotavirus strain {strain}",
            f"Rotavirus A strain {strain}",
            f"Rotavirus A {strain}",
            f"{organism} {strain}",
            f"{organism} ({strain})",
            f"{organism} isolate {strain}",
            f"{organism} strain {strain}",
        ]

    candidates: list[str] = []
    for base in base_taxonomy_names(organism):
        candidates.extend(
            [
                f"{base} {strain}",
                f"{base} ({strain})",
                f"{base} isolate {strain}",
                f"{base} strain {strain}",
            ]
        )
    return list(dict.fromkeys(candidates))


def taxonomy_names_to_try(organism: str, strain: str) -> list[str]:
    """Return all exact NCBI Taxonomy names to try for one viral dataset."""
    candidates = candidate_taxonomy_names(organism, strain)
    if organism in SPECIES_LEVEL_TAXONOMY_ORGANISMS:
        candidates.extend(base_taxonomy_names(organism))
    return list(dict.fromkeys(candidates))


def search_ncbi_taxonomy(name: str) -> list[str]:
    """Return NCBI Taxonomy IDs matching an exact All Names query."""
    query = {
        "db": "taxonomy",
        "term": f'"{name}"[All Names]',
        "retmode": "json",
        "retmax": "2",
    }
    url = f"{NCBI_ESEARCH_URL}?{urlencode(query)}"
    request = Request(url, headers={"User-Agent": "rnacentral-probing-metadata-validator"})
    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    result = data.get("esearchresult", {})
    return [str(taxon_id) for taxon_id in result.get("idlist", [])]


TaxonomySearch = Callable[[str], list[str]]


def resolve_viral_taxonomy(
    organism: str,
    strain: str,
    search: TaxonomySearch = search_ncbi_taxonomy,
) -> tuple[str, list[str]] | None:
    """Return the matched candidate name and taxon IDs, or None if unresolved."""
    for candidate in taxonomy_names_to_try(organism, strain):
        taxon_ids = search(candidate)
        if taxon_ids:
            return candidate, taxon_ids
        time.sleep(NCBI_REQUEST_DELAY_SECONDS)
    return None


def validate_metadata_file(
    path: Path,
    search: TaxonomySearch = search_ncbi_taxonomy,
) -> list[str]:
    """Return viral NCBI Taxonomy validation issues for one YAML file."""
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:
        return [f"{path}: failed to parse YAML ({exc})"]

    if not isinstance(data, dict):
        return [f"{path}: top-level YAML must be a mapping"]

    organism = str(data.get("organism", "")).strip()
    if organism not in VIRAL_ORGANISMS:
        return []

    strain = str(data.get("strain", "")).strip()
    if not strain:
        return [f"{path}: viral organism '{organism}' requires top-level strain"]

    resolved = resolve_viral_taxonomy(organism, strain, search=search)
    if resolved is None:
        tried = "; ".join(taxonomy_names_to_try(organism, strain))
        return [
            f"{path}: organism '{organism}' with strain '{strain}' did not resolve "
            f"to NCBI Taxonomy. Tried: {tried}"
        ]

    candidate, taxon_ids = resolved
    if len(taxon_ids) > 1:
        return [
            f"{path}: organism '{organism}' with strain '{strain}' resolved "
            f"ambiguously as '{candidate}' with NCBI Taxonomy IDs: {', '.join(taxon_ids)}"
        ]

    return []


def validate_metadata_files(
    paths: list[Path],
    search: TaxonomySearch = search_ncbi_taxonomy,
) -> list[str]:
    """Return validation issues across all provided YAML files."""
    issues: list[str] = []
    for path in paths:
        issues.extend(validate_metadata_file(path, search=search))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yamls", nargs="+", type=Path, help="Metadata YAML files to validate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues = validate_metadata_files(args.yamls)
    if issues:
        print("NCBI Taxonomy validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"NCBI Taxonomy validation passed for {len(args.yamls)} metadata file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
