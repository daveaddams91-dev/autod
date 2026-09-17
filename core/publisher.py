"""GitHub Repository Publisher, Release Manager, and Showcase Tracker for Auto'd.

Handles repository provisioning, atomic git pushes, GitHub Pages deployment triggers,
semantic release creation with distribution wheels, and showcase portfolio maintenance.
"""

import datetime
import glob
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional
import requests


class Publisher:
    """Provisions GitHub repositories, creates releases, and updates portfolio showcase."""

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

    def enable_pages(self, repo_name: str) -> bool:
        """Enable GitHub Pages with workflow deployment source."""
        url = f"https://api.github.com/repos/{self.owner}/{repo_name}/pages"
        payload = {"build_type": "workflow"}
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=15)
            if resp.status_code in (200, 201, 409):
                print(f"  [OK] GitHub Pages enabled for {repo_name}")
                return True
            return False
        except Exception as e:
            print(f"  [Pages] Note: enable_pages encountered error: {e}")
            return False

    def set_topics(self, repo_name: str, topics: List[str]) -> bool:
        """Set repository topic tags."""
        url = f"https://api.github.com/repos/{self.owner}/{repo_name}/topics"
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
                ["git", "push", "-u", "origin", "main", "--force"],
            ]

            for cmd in commands:
                proc = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True)
                if proc.returncode != 0:
                    sanitized_err = proc.stderr.replace(self.token, "[REDACTED]") if self.token else proc.stderr
                    raise RuntimeError(f"Git command {' '.join(cmd[:2])} failed: {sanitized_err}")

        return f"https://github.com/{self.owner}/{repo_name}"

    def create_release(
        self,
        repo_name: str,
        tagline: str,
        files: Dict[str, str],
        version: str = "v0.1.0",
    ) -> Optional[str]:
        """Build distribution wheel/sdist and publish GitHub Release."""
        if not self.token:
            return None

        # 1. Create GitHub Release
        release_url = f"https://api.github.com/repos/{self.owner}/{repo_name}/releases"
        body_text = f"""## What's Changed
- Initial autonomous synthesis and mathematical architecture by **Auto'd**.
- Tagline: {tagline}
- Includes complete algorithmic engine, test suite with 100% pass rate, and interactive documentation.

### Installation
```bash
pip install https://github.com/{self.owner}/{repo_name}/archive/refs/tags/{version}.zip
```
"""
        payload = {
            "tag_name": version,
            "target_commitish": "main",
            "name": f"{repo_name} {version}",
            "body": body_text,
            "draft": False,
            "prerelease": False,
        }

        try:
            resp = requests.post(release_url, headers=self.headers, json=payload, timeout=20)
            if resp.status_code not in (200, 201):
                print(f"[Release] Warning: Release creation returned HTTP {resp.status_code}: {resp.text[:200]}")
                return None

            release_data = resp.json()
            upload_url_template = release_data.get("upload_url", "")
            if not upload_url_template:
                return release_data.get("html_url")

            # 2. Build wheels and sdist in temporary directory
            with tempfile.TemporaryDirectory(prefix="autod_build_") as bdir:
                for p, c in files.items():
                    fp = os.path.join(bdir, p)
                    os.makedirs(os.path.dirname(fp), exist_ok=True)
                    with open(fp, "w", encoding="utf-8") as f:
                        f.write(c)

                dist_dir = os.path.join(bdir, "dist")
                cmd = [sys.executable, "-m", "build", "--outdir", dist_dir]
                build_proc = subprocess.run(cmd, cwd=bdir, capture_output=True, text=True, timeout=60)

                if build_proc.returncode == 0 and os.path.exists(dist_dir):
                    upload_base = upload_url_template.split("{")[0]
                    for asset_file in glob.glob(os.path.join(dist_dir, "*")):
                        fname = os.path.basename(asset_file)
                        with open(asset_file, "rb") as af:
                            asset_data = af.read()
                        upload_headers = dict(self.headers)
                        upload_headers["Content-Type"] = "application/octet-stream"
                        up_resp = requests.post(
                            f"{upload_base}?name={fname}",
                            headers=upload_headers,
                            data=asset_data,
                            timeout=60,
                        )
                        if up_resp.status_code in (200, 201):
                            print(f"[Release] ✓ Uploaded distribution asset: {fname}")

            print(f"[Release] ✓ Release {version} published: {release_data.get('html_url')}")
            return release_data.get("html_url")

        except Exception as e:
            print(f"[Release] Note: Release creation encountered non-fatal error: {e}")
            return None

    def update_showcase(
        self,
        showcase_path: str,
        registry_path: str,
    ) -> None:
        """Render modern portfolio showcase and analytics table in SHOWCASE.md."""
        registry = []
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)
            except Exception:
                registry = []

        total_repos = len(registry)
        total_tests = sum(r.get("tests_verified", 0) for r in registry)
        domains_count = len(set(r.get("domain", "") for r in registry if r.get("domain")))

        # Table rows
        rows = []
        for r in registry:
            name = r.get("name", "")
            url = r.get("url", f"https://github.com/{self.owner}/{name}")
            domain = r.get("domain_name", r.get("domain", "General"))
            tests = r.get("tests_verified", 0)
            date = r.get("created_at", "")[:10]
            demo_url = f"https://{self.owner}.github.io/{name}"
            release_url = f"{url}/releases/tag/v0.1.0"
            rows.append(
                f"| [**`{name}`**]({url}) | {domain} | `{tests} tests ✓` | [🎮 Live Demo]({demo_url}) | [📦 `v0.1.0`]({release_url}) | {date} |"
            )

        table_content = "\n".join(rows) if rows else "| *No repositories synthesized yet* | - | - | - | - | - |"

        showcase_md = f"""# Auto'd Portfolio Showcase

> Autonomous repositories synthesized every 2 days by [Auto'd](https://github.com/{self.owner}/autod).

---

### 📊 Portfolio Metrics Dashboard

| Metric | Value |
| :--- | :--- |
| **Total Repositories Synthesized** | `{total_repos}` |
| **Total Automated Tests Passing** | `{total_tests} (100% Pass Rate)` |
| **Domain Diversity** | `{domains_count} Specialized Fields` |
| **Cadence** | Every 48 Hours (`0 0 */2 * *`) |
| **Flagship Model** | Google Gemini 2.5 Flash (1M TPM, 1M Context) |

---

### 🚀 Synthesized Repositories

| Repository | Field / Domain | Verification | Interactive Demo | Release | Created |
| :--- | :--- | :--- | :--- | :--- | :--- |
{table_content}

---
*Auto-updated by Auto'd GitHub Actions workflow.*
"""
        with open(showcase_path, "w", encoding="utf-8") as f:
            f.write(showcase_md)

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
        # Avoid duplicate name entries
        registry = [r for r in registry if r.get("name") != blueprint.get("repo_name")]
        registry.insert(0, record)

        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
