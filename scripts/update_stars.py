#!/usr/bin/env python3
"""Update GitHub star counts in domain YAML files."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json
import os

import yaml


def get_github_stars(repo: str, token: str | None = None) -> int | None:
    """Fetch star count for a GitHub repo (e.g. 'owner/repo')."""
    url = f"https://api.github.com/repos/{repo}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("stargazers_count")
    except HTTPError as e:
        print(f"  [WARN] {repo}: HTTP {e.code}")
        return None
    except Exception as e:
        print(f"  [WARN] {repo}: {e}")
        return None


def update_domain_file(path: Path, token: str | None = None, dry_run: bool = False) -> int:
    """Update star counts in a single domain YAML file. Returns number of updates."""
    with path.open() as f:
        data = yaml.safe_load(f)

    updated = 0
    for method in data.get("methods", []):
        code = method.get("code")
        if not code:
            continue

        stars = get_github_stars(code, token)
        if stars is not None:
            old_stars = method.get("stars")
            if old_stars != stars:
                print(f"  {method['name']}: {old_stars} -> {stars}")
                method["stars"] = stars
                updated += 1
            else:
                print(f"  {method['name']}: {stars} (unchanged)")
        time.sleep(0.5)  # rate limit

    if updated > 0 and not dry_run:
        with path.open("w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return updated


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Update GitHub star counts in domain YAMLs")
    parser.add_argument(
        "--dir",
        default=str(Path(__file__).parent.parent / "domains"),
        help="Path to domains directory",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--domain", help="Update only this domain (filename without .yaml)")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[WARN] GITHUB_TOKEN not set — API rate limit will be low (60 req/hr)")

    domains_dir = Path(args.dir)
    if args.domain:
        files = [domains_dir / f"{args.domain}.yaml"]
    else:
        files = sorted(domains_dir.glob("*.yaml"))

    total_updated = 0
    for path in files:
        if not path.exists():
            print(f"[ERROR] {path} not found")
            continue
        print(f"\n=== {path.stem} ===")
        total_updated += update_domain_file(path, token, args.dry_run)

    print(f"\nTotal updates: {total_updated}")
    if args.dry_run:
        print("(dry run — no files modified)")


if __name__ == "__main__":
    main()
