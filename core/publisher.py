"""GitHub Repository Publisher and Showcase Manager for Auto'd.

Handles automated repository provisioning on GitHub, atomic multi-file commits,
topic tagging, and updating the public showcase portfolio.
"""

import datetime
import json
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional
import requests


class Publisher:
    """Provisions GitHub repositories and publishes verified codebases."""

    def __init__(self, owner: str = "Raj123-0", token: Optional[str] = None):
        self.owner = owner
        self.token = token or os.environ.get("GH_TOKEN") or os.environ.get("REPO_IMPROVER_TOKEN", "")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def repo_exists(self, repo_name: str) -> bool:
        """Check if repository already exists under the owner account."""
        url = f"https://api.github.com/repos/{self.owner}/{repo_name}"
        resp = requests.get(url, headers=self.headers, timeout=10)
        return resp.status_code == 200

    def create_repository(
        self,
        repo_name: str,
        description: str,
        is_private: bool = False,
    ) -> Dict[str, Any]:
        """Create new repository via GitHub REST API."""
        url = "https://api.github.com/user/repos"
        payload = {
            "name": repo_name,
            "description": description,
            "private": is_private,
            "has_issues": True,
            "has_wiki": False,
            "auto_init": False,
        }
        resp = requests.post(url, headers=self.headers, json=payload, timeout=20)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to create repo {repo_name} (HTTP {resp.status_code}): {resp.text}")
        return resp.json()

    def set_topics(self, repo_name: str, topics: List[str]) -> bool:
        """Set repository topic tags."""
        url = f"https://api.github.com/repos/{self.owner}/{repo_name}/topics"
        # GitHub topics must be lowercase alphanumeric with hyphens, max 35 chars
        clean_topics = [
            t.lower().replace("_", "-")[:35]
            for t in topics
            if t and len(t) <= 35
        ]
        if "autod" not in clean_topics:
            clean_topics.append("autod")

        resp = requests.put(url, headers=self.headers, json={"names": clean_topics}, timeout=15)
        return resp.status_code in (200, 201)

    def publish_files(
        self,
        repo_name: str,
        files: Dict[str, str],
        commit_message: str = "feat: initial release synthesized by Auto'd",
    ) -> str:
        """Push all files to GitHub repository using local temporary git workspace."""
        clone_url = f"https://x-access-token:{self.token}@github.com/{self.owner}/{repo_name}.git"

        with tempfile.TemporaryDirectory(prefix="autod_publish_") as tmpdir:
            # Materialize files
            for rel_path, content in files.items():
                full_path = os.path.join(tmpdir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Git commands
            commands = [
                ["git", "init", "-b", "main"],
                ["git", "config", "user.name", "autod[bot]"],
                ["git", "config", "user.email", f"144442360+{self.owner}[bot]@users.noreply.github.com"],
                ["git", "add", "."],
                ["git", "commit", "-m", commit_message],
                ["git", "remote", "add", "origin", clone_url],
                ["git", "push", "-u", "origin", "main"],
            ]

            for cmd in commands:
                proc = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True)
                if proc.returncode != 0:
                    # Sanitize token from error messages
                    sanitized_err = proc.stderr.replace(self.token, "[REDACTED]") if self.token else proc.stderr
                    raise RuntimeError(f"Git command {' '.join(cmd[:2])} failed: {sanitized_err}")

        return f"https://github.com/{self.owner}/{repo_name}"

    def update_showcase(
        self,
        repo_name: str,
        tagline: str,
        domain_name: str,
        topics: List[str],
        showcase_path: str,
    ) -> None:
        """Record newly published repository in SHOWCASE.md."""
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        repo_url = f"https://github.com/{self.owner}/{repo_name}"
        topic_badges = " ".join(f"`{t}`" for t in topics[:5])

        entry = f"""
### [{repo_name}]({repo_url})
- **Domain**: {domain_name}
- **Synthesized On**: {now}
- **Description**: {tagline}
- **Tags**: {topic_badges}
- **Status**: Verified by pytest & AST sandbox ✓
"""
        if os.path.exists(showcase_path):
            with open(showcase_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = "# Auto'd Portfolio Showcase\n\nAutonomous repositories synthesized every 2 days by [Auto'd](https://github.com/Raj123-0/autod).\n\n---\n"

        # Prepend to the top of list
        marker = "---\n"
        if marker in content:
            parts = content.split(marker, 1)
            updated_content = f"{parts[0]}{marker}{entry}\n{parts[1]}"
        else:
            updated_content = f"{content}\n{entry}"

        with open(showcase_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

    def record_in_registry(
        self,
        registry_path: str,
        blueprint: Dict[str, Any],
        repo_url: str,
        test_count: int,
    ) -> None:
        """Save structured metadata to created_repos.json."""
        registry = []
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)
            except Exception:
                registry = []

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record = {
            "name": blueprint.get("repo_name"),
            "url": repo_url,
            "domain": blueprint.get("domain"),
            "domain_name": blueprint.get("domain_name"),
            "tagline": blueprint.get("tagline"),
            "topics": blueprint.get("topics", []),
            "tests_verified": test_count,
            "created_at": now_iso,
        }
        registry.insert(0, record)

        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
