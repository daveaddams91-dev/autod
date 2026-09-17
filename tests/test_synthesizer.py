"""Unit tests for Synthesizer engine."""

import ast
from core.synthesizer import Synthesizer


def test_synthesize_orbital_domain():
    synth = Synthesizer()
    bp = {
        "repo_name": "orbit-propagator",
        "package_name": "orbit_prop",
        "tagline": "Orbital mechanics engine",
        "domain": "aerospace_orbital",
    }
    files = synth._synthesize_fallback(bp)
    files["LICENSE"] = synth._generate_license()
    files[".github/workflows/ci.yml"] = synth._generate_ci_workflow("orbit_prop")

    assert "src/orbit_prop/__init__.py" in files
    assert "src/orbit_prop/orbit_prop_core.py" in files
    assert "tests/test_core.py" in files
    assert "README.md" in files
    assert "LICENSE" in files

    # Verify AST parses without error
    for path, code in files.items():
        if path.endswith(".py"):
            ast.parse(code)


def test_synthesize_physics_domain():
    synth = Synthesizer()
    bp = {
        "repo_name": "symplectic-engine",
        "package_name": "symplec",
        "domain": "numerical_physics",
    }
    files = synth._synthesize_fallback(bp)
    for path, code in files.items():
        if path.endswith(".py"):
            ast.parse(code)


def test_synthesize_math_domain():
    synth = Synthesizer()
    bp = {
        "repo_name": "pell-solver",
        "package_name": "pell_solver",
        "domain": "computational_math",
    }
    files = synth._synthesize_fallback(bp)
    for path, code in files.items():
        if path.endswith(".py"):
            ast.parse(code)


def test_synthesize_crypto_domain():
    synth = Synthesizer()
    bp = {
        "repo_name": "shamir-sss",
        "package_name": "shamir_sss",
        "domain": "crypto_algorithms",
    }
    files = synth._synthesize_fallback(bp)
    for path, code in files.items():
        if path.endswith(".py"):
            ast.parse(code)


def test_synthesize_systems_domain():
    synth = Synthesizer()
    bp = {
        "repo_name": "stack-vm",
        "package_name": "stack_vm",
        "domain": "systems_compilers",
    }
    files = synth._synthesize_fallback(bp)
    for path, code in files.items():
        if path.endswith(".py"):
            ast.parse(code)
