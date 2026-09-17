"""Verification Sandbox and Self-Healing Engine for Auto'd.

Ensures that 100% of generated code passes AST syntax parsing and automated
pytest suites before any repository is published or committed to GitHub.
"""

import ast
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .model_client import SmartModelClient


@dataclass
class VerificationResult:
    passed: bool
    test_count: int = 0
    errors: List[str] = field(default_factory=list)
    output: str = ""
    repaired_files: Optional[Dict[str, str]] = None


class Verifier:
    """Rigorous sandboxed code verifier and self-healing test engine."""

    def __init__(self, model_client: Optional[SmartModelClient] = None):
        self.client = model_client

    def verify_syntax(self, files: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Verify that all Python files parse cleanly via AST."""
        errors = []
        for path, content in files.items():
            if path.endswith(".py"):
                try:
                    ast.parse(content, filename=path)
                except SyntaxError as e:
                    errors.append(f"SyntaxError in {path}:{e.lineno}: {e.msg}")
        return (len(errors) == 0, errors)

    def run_sandbox_tests(self, files: Dict[str, str], timeout_seconds: int = 30) -> Tuple[bool, int, str]:
        """Execute pytest in an isolated temporary directory containing the generated code."""
        with tempfile.TemporaryDirectory(prefix="autod_sandbox_") as tmpdir:
            # Materialize all files
            for rel_path, content in files.items():
                full_path = os.path.join(tmpdir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Also create an empty conftest.py or setup sys.path
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{os.path.join(tmpdir, 'src')}{os.pathsep}{tmpdir}{os.pathsep}{env.get('PYTHONPATH', '')}"

            cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", "tests/"]
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=tmpdir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
                output = proc.stdout + "\n" + proc.stderr
                passed = proc.returncode == 0

                # Count passed tests
                test_count = output.count(" PASSED")
                return passed, test_count, output
            except subprocess.TimeoutExpired:
                return False, 0, f"Sandbox test execution timed out after {timeout_seconds} seconds."
            except Exception as e:
                return False, 0, f"Sandbox execution error: {str(e)}"

    def verify_and_repair(
        self,
        files: Dict[str, str],
        max_repairs: int = 2,
    ) -> VerificationResult:
        """Verify code syntax and test execution, running self-healing if needed."""
        current_files = dict(files)

        for attempt in range(max_repairs + 1):
            print(f"[Verifier] Running sandbox verification (Iteration {attempt + 1}/{max_repairs + 1})...")

            # 1. Check syntax
            syntax_ok, syntax_errors = self.verify_syntax(current_files)
            if not syntax_ok:
                print(f"[Verifier] Syntax errors detected: {syntax_errors}")
                if attempt < max_repairs and self.client:
                    current_files = self._self_heal_syntax(current_files, syntax_errors)
                    continue
                return VerificationResult(
                    passed=False,
                    errors=syntax_errors,
                    repaired_files=current_files
                )

            # 2. Run tests in sandbox
            tests_ok, test_count, test_log = self.run_sandbox_tests(current_files)
            if tests_ok:
                print(f"[Verifier] ✓ All sandbox tests passed ({test_count} tests).")
                return VerificationResult(
                    passed=True,
                    test_count=test_count,
                    output=test_log,
                    repaired_files=current_files
                )

            print(f"[Verifier] Tests failed:\n{test_log[:400]}...")
            if attempt < max_repairs and self.client:
                print(f"[Verifier] Attempting self-healing repair...")
                current_files = self._self_heal_tests(current_files, test_log)
            else:
                return VerificationResult(
                    passed=False,
                    test_count=test_count,
                    errors=[f"Pytest execution failed"],
                    output=test_log,
                    repaired_files=current_files
                )

        return VerificationResult(
            passed=False,
            errors=["Exhausted max repair attempts without passing all tests."],
            repaired_files=current_files
        )

    def _self_heal_syntax(self, files: Dict[str, str], syntax_errors: List[str]) -> Dict[str, str]:
        """Prompt model to fix syntax errors."""
        prompt = f"""
The following Python files produced syntax errors:
{syntax_errors}

Here are the broken files:
{json.dumps({k: v for k, v in files.items() if k.endswith('.py')}, indent=2)}

Please fix the syntax errors and return strictly a JSON object:
{{
  "repaired_files": {{
    "path/to/file.py": "fixed content..."
  }}
}}
"""
        try:
            res = self.client.generate_json(prompt, system_prompt="You are an expert Python syntax repair specialist.")
            repaired = res.get("repaired_files", {})
            for p, content in repaired.items():
                if p in files:
                    files[p] = content
        except Exception as e:
            print(f"[Verifier] Self-healing syntax call failed: {e}")
        return files

    def _self_heal_tests(self, files: Dict[str, str], test_output: str) -> Dict[str, str]:
        """Prompt model to fix code causing test failures."""
        prompt = f"""
Pytest failed with the following traceback:
{test_output[-1500:]}

Current codebase files:
{json.dumps({k: v for k, v in files.items() if k.endswith('.py')}, indent=2)}

Please analyze the failure and provide the corrected file contents.
Return strictly JSON:
{{
  "repaired_files": {{
    "path/to/file.py": "repaired python code..."
  }}
}}
"""
        try:
            res = self.client.generate_json(prompt, system_prompt="You are an expert Python test debugging engineer.")
            repaired = res.get("repaired_files", {})
            for p, content in repaired.items():
                if p in files:
                    files[p] = content
        except Exception as e:
            print(f"[Verifier] Self-healing tests call failed: {e}")
        return files
