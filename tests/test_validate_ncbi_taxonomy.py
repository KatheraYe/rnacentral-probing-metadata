from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "validate_ncbi_taxonomy.py"
    spec = importlib.util.spec_from_file_location("validate_ncbi_taxonomy", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_ncbi_taxonomy = _load_module()


def test_candidate_taxonomy_names_formats_influenza_strain():
    assert validate_ncbi_taxonomy.candidate_taxonomy_names(
        "Influenza A virus",
        "A/Puerto Rico/8/1934(H1N1)",
    ) == ["Influenza A virus (A/Puerto Rico/8/1934(H1N1))"]


def test_candidate_taxonomy_names_includes_ncbi_aliases():
    assert (
        "Severe acute respiratory syndrome coronavirus 2 isolate Wuhan-Hu-1"
        in validate_ncbi_taxonomy.candidate_taxonomy_names("SARS-CoV-2", "Wuhan-Hu-1")
    )


def test_validate_metadata_file_passes_when_viral_strain_resolves(tmp_path):
    yaml_path = tmp_path / "rnastruct00014.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00014\n"
            "organism: Influenza A virus\n"
            "strain: A/Puerto Rico/8/1934(H1N1)\n"
            "raw_data:\n"
            "  repository: GEO\n"
            "  accession: GSE122286\n"
            "  run_accessions: []\n"
        ),
        encoding="utf-8",
    )

    def fake_search(name: str) -> list[str]:
        if name == "Influenza A virus (A/Puerto Rico/8/1934(H1N1))":
            return ["211044"]
        return []

    assert validate_ncbi_taxonomy.validate_metadata_file(yaml_path, search=fake_search) == []


def test_validate_metadata_file_requires_strain_for_viral_organism(tmp_path):
    yaml_path = tmp_path / "rnastruct00014.yaml"
    yaml_path.write_text(
        "dataset_id: rnastruct00014\norganism: Influenza A virus\n",
        encoding="utf-8",
    )

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, search=lambda name: [])

    assert issues == [
        f"{yaml_path}: viral organism 'Influenza A virus' requires top-level strain"
    ]


def test_validate_metadata_file_reports_unresolved_strain(tmp_path):
    yaml_path = tmp_path / "rnastruct00014.yaml"
    yaml_path.write_text(
        (
            "dataset_id: rnastruct00014\n"
            "organism: Influenza A virus\n"
            "strain: Unknown\n"
        ),
        encoding="utf-8",
    )

    issues = validate_ncbi_taxonomy.validate_metadata_file(yaml_path, search=lambda name: [])

    assert len(issues) == 1
    assert "did not resolve to NCBI Taxonomy" in issues[0]
