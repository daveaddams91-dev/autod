"""Unit tests for Ideator engine."""

from core.ideator import Ideator


def test_choose_domain():
    ideator = Ideator()
    domain = ideator.choose_domain("aerospace_orbital")
    assert domain["id"] == "aerospace_orbital"
    assert "Aerospace" in domain["name"]


def test_fallback_blueprint_structure():
    ideator = Ideator()
    domain = ideator.choose_domain("computational_math")
    existing = ["py-computational_math-solver"]
    blueprint = ideator._fallback_blueprint(domain, existing)

    assert "repo_name" in blueprint
    assert blueprint["repo_name"] != "py-computational_math-solver"
    assert "package_name" in blueprint
    assert len(blueprint["planned_files"]) >= 4
    assert any("test" in f["path"] for f in blueprint["planned_files"])


def test_no_duplicate_names():
    ideator = Ideator()
    domain = ideator.choose_domain("systems_compilers")
    existing = ["py-systems_compilers-solver", "tokamak-py"]
    bp = ideator._fallback_blueprint(domain, existing)
    assert bp["repo_name"].lower() not in existing
