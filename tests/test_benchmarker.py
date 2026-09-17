"""Unit tests for Benchmarker."""

from core.benchmarker import Benchmarker


def test_generate_benchmark_script():
    script = Benchmarker.generate_benchmark_script("orbitprop", "aerospace_orbital")
    assert "def run_benchmark" in script
    assert "perf_counter" in script


def test_render_svg_chart():
    data = [(100, 0.04), (500, 0.20), (1000, 0.40)]
    svg = Benchmarker.render_svg_chart("Test Scalability", data)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Test Scalability" in svg
    assert "Execution Latency" in svg


def test_inject_benchmark_section():
    readme = "# Test Project\n\nSome intro text.\n\n## License\nMIT License\n"
    updated = Benchmarker.inject_benchmark_section(readme, "test-project")
    assert "## Performance & Scalability Benchmarks" in updated
    assert "assets/benchmark.svg" in updated
    assert "## License" in updated
