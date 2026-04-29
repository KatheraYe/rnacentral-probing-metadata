from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_YAML = REPO_ROOT / "schema" / "rnastruct.schema.yaml"


def organism_pattern() -> re.Pattern[str]:
    with SCHEMA_YAML.open(encoding="utf-8") as handle:
        schema = yaml.safe_load(handle)
    pattern = schema["classes"]["Dataset"]["attributes"]["organism"]["pattern"]
    return re.compile(pattern)


def test_organism_pattern_accepts_latin_names_and_curated_viral_names():
    pattern = organism_pattern()

    assert pattern.fullmatch("Homo sapiens")
    assert pattern.fullmatch("Mus musculus castaneus")
    assert pattern.fullmatch("Influenza A virus")
    assert pattern.fullmatch("SARS-CoV-2")
    assert pattern.fullmatch("Zika virus")
    assert pattern.fullmatch("HIV")
    assert pattern.fullmatch("Rotavirus A")


def test_organism_pattern_rejects_unstructured_names():
    pattern = organism_pattern()

    assert pattern.fullmatch("not a species") is None
    assert pattern.fullmatch("Influenza") is None
