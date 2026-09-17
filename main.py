"""Auto'd — Autonomous Repository Synthesizer CLI.

Generates and publishes a brand-new, production-ready, fully verified GitHub repository.
"""

import argparse
import os
import sys
from typing import Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.bridge import EcosystemBridge
from core.ideator import Ideator
from core.model_client import SmartModelClient
from core.notifier import NotificationDispatcher
from core.publisher import Publisher
from core.synthesizer import Synthesizer
from core.verifier import Verifier


def run_pipeline(
    domain: Optional[str] = None,
    custom_name: Optional[str] = None,
    dry_run: bool = False,
    output_dir: Optional[str] = None,
) -> int:
    """Execute the full end-to-end Auto'd pipeline."""
    print("=" * 65)
    print(">> Auto'd -- Autonomous Repository Synthesizer")
    print("=" * 65)

    client = SmartModelClient()
    ideator = Ideator(model_client=client)
    synthesizer = Synthesizer(model_client=client)
    verifier = Verifier(model_client=client)
    publisher = Publisher()

    # Step 1: Ideate concept
    print("\n[Phase 1] Brainstorming novel concept...")
    blueprint = ideator.brainstorm(domain_id=domain)
    if custom_name:
        blueprint["repo_name"] = custom_name
        blueprint["package_name"] = custom_name.replace("-", "_")

    print(f"  -> Repository: {blueprint.get('repo_name')}")
    print(f"  -> Domain:     {blueprint.get('domain_name')}")
    print(f"  -> Tagline:    {blueprint.get('tagline')}")
    print(f"  -> Topics:     {', '.join(blueprint.get('topics', []))}")

    # Step 2: Synthesize codebase
    print("\n[Phase 2] Synthesizing complete multi-file codebase...")
    files = synthesizer.synthesize_repository(blueprint)
    print(f"  -> Generated {len(files)} files:")
    for path in sorted(files.keys()):
        print(f"     * {path} ({len(files[path].splitlines())} lines)")

    # Save to local output dir if requested
    if output_dir:
        dest_dir = os.path.join(output_dir, blueprint.get("repo_name"))
        print(f"\n[Export] Writing generated repository to {dest_dir}...")
        for p, c in files.items():
            full = os.path.join(dest_dir, p)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(c)

    # Step 3: Verify and self-heal
    print("\n[Phase 3] Running sandboxed AST and pytest verification...")
    result = verifier.verify_and_repair(files, max_repairs=2)
    if not result.passed:
        print(f"\n[FAIL] Pre-publication verification failed: {result.errors}")
        print(f"Test Logs:\n{result.output}")
        return 1

    print(f"\n[OK] Verification PASSED with {result.test_count} automated tests!")
    final_files = result.repaired_files or files

    # Step 4: Dry-run check
    if dry_run:
        print("\n[Dry Run] Completed successfully without publishing to GitHub.")
        print(f"Target repository would have been: https://github.com/{publisher.owner}/{blueprint.get('repo_name')}")
        return 0

    # Step 5: Publish to GitHub
    repo_name = blueprint.get("repo_name")
    tagline = blueprint.get("tagline")
    print(f"\n[Phase 4] Publishing to GitHub (Raj123-0/{repo_name})...")

    token = os.environ.get("GH_TOKEN") or os.environ.get("REPO_IMPROVER_TOKEN")
    if not token:
        print("[ERROR] Error: GH_TOKEN or REPO_IMPROVER_TOKEN must be set to publish to GitHub.")
        return 1

    try:
        if not publisher.repo_exists(repo_name):
            print("  -> Creating repository on GitHub...")
            publisher.create_repository(repo_name, tagline)
        else:
            print(f"  -> Repository {repo_name} already exists on GitHub, updating...")

        print("  -> Setting topic tags...")
        publisher.set_topics(repo_name, blueprint.get("topics", []))

        print("  -> Enabling GitHub Pages deployment...")
        publisher.enable_pages(repo_name)

        print("  -> Pushing verified files to main branch...")
        repo_url = publisher.publish_files(repo_name, final_files)
        print(f"  [OK] Successfully published: {repo_url}")

        # Step 6: Create GitHub Release with distribution wheels
        print("  -> Building package wheels and creating GitHub Release v0.1.0...")
        release_url = publisher.create_release(repo_name, tagline, final_files, version="v0.1.0")

        # Step 7: Ecosystem Bridge (Auto-handoff to repo-improver-bot)
        print("  -> Handoff to repo-improver-bot ecosystem...")
        bridge = EcosystemBridge(owner=publisher.owner, token=token)
        bridge.register_new_repo(
            new_repo_name=repo_name,
            domain_id=blueprint.get("domain", "general_python"),
            description=tagline,
        )

        # Step 8: Update showcase and registry
        showcase_path = os.path.join(os.path.dirname(__file__), "SHOWCASE.md")
        registry_path = os.path.join(os.path.dirname(__file__), "created_repos.json")

        publisher.record_in_registry(
            registry_path=registry_path,
            blueprint=blueprint,
            repo_url=repo_url,
            test_count=result.test_count,
        )
        publisher.update_showcase(
            showcase_path=showcase_path,
            registry_path=registry_path,
        )
        print("  [OK] Updated SHOWCASE.md and created_repos.json")

        # Step 9: Post notification digest & webhooks
        print("  -> Dispatching notifications...")
        notifier = NotificationDispatcher(owner=publisher.owner, token=token)
        notifier.post_github_digest(blueprint, repo_url, result.test_count)
        notifier.send_discord_notification(blueprint, repo_url, result.test_count)
        print("  [OK] Notifications dispatched successfully!")
        return 0

    except Exception as e:
        print(f"[ERROR] Failed to publish repository: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Auto'd — Autonomous Repository Synthesizer")
    parser.add_argument("--domain", help="Target domain (e.g. aerospace_orbital, numerical_physics, computational_math)")
    parser.add_argument("--name", help="Custom name for the new repository")
    parser.add_argument("--dry-run", action="store_true", help="Simulate generation and test verification without creating GitHub repo")
    parser.add_argument("--output-dir", help="Directory path to export generated repository locally")

    args = parser.parse_args()
    exit_code = run_pipeline(
        domain=args.domain,
        custom_name=args.name,
        dry_run=args.dry_run,
        output_dir=args.output_dir,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
