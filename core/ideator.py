"""Ideation and Concept Engine for Auto'd.

Brainstorms novel, production-grade repository concepts aligned with user interest domains
(Aerospace, Numerical Physics, Computational Math, Systems, Cryptography) while guaranteeing
zero name or concept collisions with existing repositories.
"""

import json
import os
import random
import re
from typing import Any, Dict, List, Optional
import requests

from .model_client import SmartModelClient


class Ideator:
    """Invents novel repository concepts tailored to the user's technical domains."""

    def __init__(self, model_client: Optional[SmartModelClient] = None, config_path: Optional[str] = None):
        self.client = model_client or SmartModelClient(config_path)
        self.config = self.client.config
        self.owner = self.config.get("github_owner", "Raj123-0")
        self.domains = self.config.get("domains", [])

    def get_existing_repos(self, token: Optional[str] = None) -> List[str]:
        """Fetch list of all public and private repositories for the user to prevent duplication."""
        token = token or os.environ.get("GH_TOKEN") or os.environ.get("REPO_IMPROVER_TOKEN")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        repos = []
        page = 1
        while True:
            url = f"https://api.github.com/users/{self.owner}/repos?per_page=100&page={page}"
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                if not data or not isinstance(data, list):
                    break
                for r in data:
                    name = r.get("name")
                    if name:
                        repos.append(name.lower())
                page += 1
                if len(data) < 100:
                    break
            except Exception:
                break

        return repos

    def choose_domain(self, preferred_domain: Optional[str] = None) -> Dict[str, Any]:
        """Select target domain for the new repository."""
        if preferred_domain:
            for d in self.domains:
                if d.get("id") == preferred_domain or d.get("name").lower() == preferred_domain.lower():
                    return d

        if not self.domains:
            return {
                "id": "computational_math",
                "name": "Computational Mathematics & Number Theory",
                "description": "High precision mathematics, continuous fractions, and algorithmic number theory."
            }

        return random.choice(self.domains)

    def brainstorm(
        self,
        domain_id: Optional[str] = None,
        existing_repos: Optional[List[str]] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Use the smart model to brainstorm a novel, verified repository concept."""
        domain = self.choose_domain(domain_id)
        if existing_repos is None:
            existing_repos = self.get_existing_repos(token)

        existing_names_sample = existing_repos[:50]

        system_prompt = (
            "You are an elite research scientist and open-source software architect. "
            "Your mission is to devise a brand-new, cutting-edge, realistic Python repository concept. "
            "The repository MUST be genuine, practical, mathematically rigorous, and cleanly structured. "
            "Never invent trivial toy scripts. Design a complete, standalone Python package that researchers "
            "or developers would star and use."
        )

        user_prompt = f"""
We need to synthesize a brand-new GitHub repository under the user '{self.owner}'.

Domain Focus: {domain.get('name')}
Domain Description: {domain.get('description')}

Existing repositories that you must NOT duplicate or closely copy:
{json.dumps(existing_names_sample)}

Requirements for the new repository:
1. 'repo_name': Kebab-case, memorable, max 32 characters, strictly alphanumeric and hyphens (e.g. 'orbital-propagator', 'lattice-sieve', 'symplectic-integrator').
2. 'package_name': Snake_case Python package identifier (e.g. 'orbitprop', 'latticesieve').
3. 'tagline': A punchy 1-line description of what this package solves (max 120 chars).
4. 'topics': 4-6 relevant GitHub topics (e.g. ['orbital-mechanics', 'kepler', 'astrodynamics', 'python']).
5. 'architecture_summary': 2-3 sentences describing the algorithmic foundation and module design.
6. 'planned_files': A list of files to construct. Must include:
   - 'src/<package_name>/__init__.py'
   - 'src/<package_name>/core.py' (or domain-specific main engine)
   - 'src/<package_name>/utils.py' (or math/data helpers)
   - 'tests/test_core.py' (comprehensive pytest suite)
   - 'README.md'
   - 'pyproject.toml'

Return strictly JSON matching this structure:
{{
  "repo_name": "...",
  "package_name": "...",
  "tagline": "...",
  "domain": "{domain.get('id')}",
  "topics": ["..."],
  "architecture_summary": "...",
  "planned_files": [
    {{"path": "src/...", "purpose": "..."}},
    {{"path": "tests/...", "purpose": "..."}}
  ]
}}
"""
        try:
            blueprint = self.client.generate_json(user_prompt=user_prompt, system_prompt=system_prompt)
            # Validate repo_name
            repo_name = re.sub(r"[^a-zA-Z0-9_-]", "-", blueprint.get("repo_name", "")).strip("-").lower()
            if not repo_name or repo_name in existing_repos:
                repo_name = f"{domain.get('id', 'repo')}-engine"

            package_name = re.sub(r"[^a-zA-Z0-9_]", "_", blueprint.get("package_name", "")).strip("_").lower()
            if not package_name:
                package_name = repo_name.replace("-", "_")

            blueprint["repo_name"] = repo_name
            blueprint["package_name"] = package_name
            blueprint["domain_name"] = domain.get("name")
            return blueprint
        except Exception as e:
            print(f"[Ideator] Model generation failed ({e}). Using robust fallback blueprint...")
            return self._fallback_blueprint(domain, existing_repos)

    def _fallback_blueprint(self, domain: Dict[str, Any], existing_repos: List[str]) -> Dict[str, Any]:
        """Deterministic offline fallback blueprint in case of network or API failure."""
        slug = domain.get("id", "math")
        name = f"py-{slug}-solver"
        if name.lower() in existing_repos:
            name = f"py-{slug}-{random.randint(100, 999)}"

        pkg = name.replace("-", "_")
        return {
            "repo_name": name,
            "package_name": pkg,
            "tagline": f"High-performance {domain.get('name')} engine with mathematical verification and clean Pythonic API.",
            "domain": domain.get("id"),
            "domain_name": domain.get("name"),
            "topics": [domain.get("id"), "python", "algorithms", "scientific-computing", "autod"],
            "architecture_summary": "Clean modular architecture with vectorized numerical solvers, rigorous convergence tests, and error bounds.",
            "planned_files": [
                {"path": f"src/{pkg}/__init__.py", "purpose": "Package exports and version definition"},
                {"path": f"src/{pkg}/engine.py", "purpose": "Core numerical routines and solvers"},
                {"path": f"src/{pkg}/models.py", "purpose": "Data classes and mathematical structures"},
                {"path": "tests/test_engine.py", "purpose": "Automated pytest verification suite"},
                {"path": "README.md", "purpose": "Documentation and usage examples"},
                {"path": "pyproject.toml", "purpose": "Packaging metadata and dependencies"}
            ]
        }
