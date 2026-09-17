"""Unit tests for Verifier engine."""

from core.verifier import Verifier
from core.synthesizer import Synthesizer


def test_verify_syntax_clean():
    verifier = Verifier()
    files = {
        "src/calc/core.py": "def add(a: int, b: int) -> int:\n    return a + b\n",
        "tests/test_calc.py": "def test_add():\n    assert 1 + 1 == 2\n",
    }
    ok, errors = verifier.verify_syntax(files)
    assert ok is True
    assert len(errors) == 0


def test_verify_syntax_broken():
    verifier = Verifier()
    files = {
        "src/broken.py": "def broken(:\n    pass",
    }
    ok, errors = verifier.verify_syntax(files)
    assert ok is False
    assert len(errors) == 1
    assert "SyntaxError" in errors[0]


def test_sandbox_test_runner():
    synth = Synthesizer()
    verifier = Verifier()
    bp = {
        "repo_name": "orbit-test",
        "package_name": "orbit_test",
        "domain": "aerospace_orbital",
    }
    files = synth._synthesize_fallback(bp)
    passed, test_count, log = verifier.run_sandbox_tests(files)
    assert passed is True
    assert test_count >= 3
