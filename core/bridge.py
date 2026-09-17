"""Ecosystem Bridge between Auto'd and repo-improver-bot.

Automatically registers newly synthesized repositories in repo-improver-bot's
active registry so they immediately enter the continuous 24/7 capability ladder.
"""

import base64
import json
import os
from typing import Any, Dict, Optional
import requests


class EcosystemBridge:
    """Handoff engine connecting Auto'd to repo-improver-bot."""

    def __init__(self, owner: str = "Raj123-0", bot_repo: str = "repo-improver-bot", token: Optional[str] = None):
        self.owner = owner
        self.bot_repo = bot_repo
        self.token = token or os.environ.get("GH_TOKEN") or os.environ.get("REPO_IMPROVER_TOKEN", "")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def register_new_repo(
        self,
        new_repo_name: str,
        domain_id: str,
        description: str = "",
        language: str = "Python",
    ) -> bool:
        """Fetch repo-improver-bot's registry, add the new repo, and commit back."""
        if not self.token:
            print("[Bridge] Warning: No token provided; skipping ecosystem bridge registration.")
            return False

        url = f"https://api.github.com/repos/{self.owner}/{self.bot_repo}/contents/repo_registry.json"
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code != 200:
                print(f"[Bridge] Warning: Could not fetch repo_registry.json (HTTP {resp.status_code})")
                return False

            data = resp.json()
            sha = data.get("sha")
            raw_content = base64.b64decode(data.get("content", "")).decode("utf-8")
            registry = json.loads(raw_content)

            if new_repo_name in registry:
                print(f"[Bridge] Repository {new_repo_name} already registered in repo-improver-bot.")
                return True

            # Register entry for continuous improvement
            registry[new_repo_name] = {
                "description": description,
                "domain": domain_id,
                "improvements_count": 0,
                "language": language,
                "last_improved_at": None,
                "pr_history": [],
                "stages_completed": []
            }

            # Commit back to main
            updated_json = json.dumps(registry, indent=2, sort_keys=True)
            encoded = base64.b64encode(updated_json.encode("utf-8")).decode("utf-8")

            payload = {
                "message": f"chore(registry): register new Auto'd repo '{new_repo_name}' for autonomous improvement",
                "content": encoded,
                "sha": sha,
                "branch": "main",
            }
            put_resp = requests.put(url, headers=self.headers, json=payload, timeout=20)
            if put_resp.status_code in (200, 201):
                print(f"[Bridge] [OK] Successfully registered '{new_repo_name}' in repo-improver-bot!")
                return True
            else:
                print(f"[Bridge] Failed to commit updated registry (HTTP {put_resp.status_code}): {put_resp.text[:200]}")
                return False

        except Exception as e:
            print(f"[Bridge] Error registering in repo-improver-bot: {e}")
            return False
