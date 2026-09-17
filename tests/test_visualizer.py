"""Unit tests for VisualizerGenerator."""

from core.visualizer import VisualizerGenerator


def test_generate_orbital_demo():
    bp = {"repo_name": "orbit-sim", "domain": "aerospace_orbital", "tagline": "Orbital Demo"}
    html = VisualizerGenerator.generate_demo(bp)
    assert "<!DOCTYPE html>" in html
    assert "orbitCanvas" in html
    assert "Semi-Major Axis" in html
    assert "orbit-sim" in html


def test_generate_physics_demo():
    bp = {"repo_name": "verlet-sim", "domain": "numerical_physics", "tagline": "Physics Demo"}
    html = VisualizerGenerator.generate_demo(bp)
    assert "<!DOCTYPE html>" in html
    assert "simCanvas" in html
    assert "Hamiltonian" in html


def test_generate_math_demo():
    bp = {"repo_name": "cf-calc", "domain": "computational_math", "tagline": "Math Demo"}
    html = VisualizerGenerator.generate_demo(bp)
    assert "<!DOCTYPE html>" in html
    assert "Continued Fraction" in html


def test_generate_systems_demo():
    bp = {"repo_name": "vm-repl", "domain": "systems_compilers", "tagline": "VM Demo"}
    html = VisualizerGenerator.generate_demo(bp)
    assert "<!DOCTYPE html>" in html
    assert "StackVM" in html


def test_generate_crypto_demo():
    bp = {"repo_name": "shamir-app", "domain": "crypto_algorithms", "tagline": "Crypto Demo"}
    html = VisualizerGenerator.generate_demo(bp)
    assert "<!DOCTYPE html>" in html
    assert "Threshold Secret Sharing" in html
