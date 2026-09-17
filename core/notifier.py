"""Notification and Portfolio Digest Dispatcher for Auto'd.

Posts updates to GitHub Issue digests and optional webhooks (Discord / Telegram)
whenever a new repository is synthesized and verified.
"""

import datetime
import json
import os
from typing import Any, Dict, Optional
import requests


class NotificationDispatcher:
    """Dispatches real-time alerts across GitHub, Discord, and Telegram."""

    def __init__(self, owner: str = "Raj123-0", repo: str = "autod", token: Optional[str] = None):
        self.owner = owner
        self.repo = repo
        self.token = token or os.environ.get("GH_TOKEN") or os.environ.get("REPO_IMPROVER_TOKEN", "")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def post_github_digest(self, blueprint: Dict[str, Any], repo_url: str, test_count: int) -> bool:
        """Create or comment on a persistent Portfolio Activity Digest issue in autod."""
        if not self.token:
            return False

        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        repo_name = blueprint.get("repo_name")
        domain_name = blueprint.get("domain_name", "Computational Science")
        tagline = blueprint.get("tagline", "")
        demo_url = f"https://{self.owner}.github.io/{repo_name}"

        comment_body = f"""### 🚀 New Repository Synthesized: [{repo_name}]({repo_url})

- **Domain**: {domain_name}
- **Timestamp**: {now}
- **Description**: {tagline}
- **Test Verification**: `{test_count} tests passing (100%)` ✓
- **Live Demo**: [Open Interactive Simulation]({demo_url})
- **GitHub Release**: [`v0.1.0`]({repo_url}/releases/tag/v0.1.0)
"""
        # Find existing digest issue
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues?state=open"
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            digest_issue_num = None
            if resp.status_code == 200:
                for issue in resp.json():
                    if "Portfolio Activity Digest" in issue.get("title", ""):
                        digest_issue_num = issue.get("number")
                        break

            if digest_issue_num:
                # Add comment to existing issue
                comment_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{digest_issue_num}/comments"
                post_resp = requests.post(comment_url, headers=self.headers, json={"body": comment_body}, timeout=15)
                return post_resp.status_code in (200, 201)
            else:
                # Create the digest issue
                create_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"
                payload = {
                    "title": "🚀 Portfolio Activity Digest — Auto'd Synthesizer",
                    "body": f"# Auto'd Portfolio Activity Log\n\nContinuous log of verified repositories published every 2 days.\n\n---\n{comment_body}",
                    "labels": ["autod", "portfolio-digest"],
                }
                post_resp = requests.post(create_url, headers=self.headers, json=payload, timeout=15)
                return post_resp.status_code in (200, 201)

        except Exception as e:
            print(f"[Notifier] Error updating GitHub digest issue: {e}")
            return False

    def send_discord_notification(self, blueprint: Dict[str, Any], repo_url: str, test_count: int) -> bool:
        """Send Discord embed webhook if DISCORD_WEBHOOK_URL is configured."""
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            return False

        payload = {
            "embeds": [{
                "title": f"🚀 Auto'd Born: {blueprint.get('repo_name')}",
                "url": repo_url,
                "description": blueprint.get("tagline"),
                "color": 0x38bdf8,
                "fields": [
                    {"name": "Domain", "value": blueprint.get("domain_name", "General"), "inline": True},
                    {"name": "Tests", "value": f"{test_count} passing ✓", "inline": True},
                    {"name": "Live Demo", "value": f"[Interactive Simulation](https://{self.owner}.github.io/{blueprint.get('repo_name')})", "inline": False},
                ],
                "footer": {"text": "Auto'd 24/7 Autonomous Synthesizer"},
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }]
        }
        try:
            r = requests.post(webhook_url, json=payload, timeout=10)
            return r.status_code in (200, 204)
        except Exception:
            return False
