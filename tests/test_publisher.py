"""Unit tests for Publisher engine."""

import json
import os
import tempfile
from core.publisher import Publisher


def test_update_showcase():
    pub = Publisher(owner="Raj123-0", token="dummy-token")
    with tempfile.TemporaryDirectory() as tmpdir:
        showcase_path = os.path.join(tmpdir, "SHOWCASE.md")
        reg_path = os.path.join(tmpdir, "created_repos.json")
        bp = {
            "repo_name": "kepler-solver",
            "tagline": "Fast Kepler equation solver in pure Python",
            "domain": "aerospace_orbital",
            "domain_name": "Aerospace & Orbital Mechanics",
            "topics": ["astrodynamics", "kepler", "python"],
        }
        pub.record_in_registry(reg_path, bp, "https://github.com/Raj123-0/kepler-solver", 4)
        pub.update_showcase(showcase_path=showcase_path, registry_path=reg_path)

        with open(showcase_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "kepler-solver" in content
        assert "Aerospace & Orbital Mechanics" in content
        assert "Portfolio Metrics Dashboard" in content


def test_record_in_registry():
    pub = Publisher(owner="Raj123-0", token="dummy-token")
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_path = os.path.join(tmpdir, "created_repos.json")
        bp = {
            "repo_name": "symplectic-nbody",
            "domain": "numerical_physics",
            "domain_name": "Computational Physics",
            "tagline": "N-body symplectic integrator",
            "topics": ["physics", "n-body"],
        }
        pub.record_in_registry(reg_path, bp, "https://github.com/Raj123-0/symplectic-nbody", 5)

        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["name"] == "symplectic-nbody"
        assert data[0]["tests_verified"] == 5
