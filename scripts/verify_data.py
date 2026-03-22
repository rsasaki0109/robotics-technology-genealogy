#!/usr/bin/env python3
"""Verify domain YAML data against external APIs (arXiv, GitHub, Semantic Scholar)."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import yaml

DOMAINS_DIR = Path(__file__).parent.parent / "domains"
REPORT_PATH = Path(__file__).parent.parent / "docs" / "verification_report.json"


def fetch_json(url: str, headers: dict | None = None, timeout: int = 10) -> dict | None:
    headers = headers or {}
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        return {"error": e.code}
    except Exception as e:
        return {"error": str(e)}


def verify_arxiv(arxiv_id: str) -> dict:
    """Verify arXiv ID exists and return paper title."""
    # Use arXiv API
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    req = Request(url)
    try:
        with urlopen(req, timeout=10) as resp:
            content = resp.read().decode()
        # Simple XML parsing for title
        if "<title>Error</title>" in content:
            return {"valid": False, "error": "not_found"}
        # Extract title (between <title> tags, skip the first one which is the feed title)
        titles = re.findall(r"<title>(.*?)</title>", content, re.DOTALL)
        if len(titles) >= 2:
            title = titles[1].strip().replace("\n", " ")
            return {"valid": True, "title": title}
        return {"valid": False, "error": "parse_error"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def verify_github(repo: str, token: str | None = None) -> dict:
    """Verify GitHub repo exists and return star count."""
    url = f"https://api.github.com/repos/{repo}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    data = fetch_json(url, headers)
    if data is None:
        return {"valid": False, "error": "timeout"}
    if "error" in data:
        return {"valid": False, "error": data["error"]}
    return {
        "valid": True,
        "stars": data.get("stargazers_count"),
        "description": data.get("description", ""),
    }


def verify_all(domains_dir: Path, token: str | None = None, quick: bool = False) -> dict:
    """Verify all methods across all domains."""
    results = {
        "total_methods": 0,
        "arxiv_checked": 0,
        "arxiv_valid": 0,
        "arxiv_invalid": [],
        "github_checked": 0,
        "github_valid": 0,
        "github_invalid": [],
        "year_mismatches": [],
        "domains": {},
    }

    for path in sorted(domains_dir.glob("*.yaml")):
        with path.open() as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        domain_name = data.get("name", path.stem)
        domain_results = {"methods": []}

        for m in data.get("methods", []):
            results["total_methods"] += 1
            method_result = {"name": m["name"], "issues": []}

            # Verify arXiv
            arxiv_id = m.get("arxiv")
            if arxiv_id:
                results["arxiv_checked"] += 1
                arxiv_result = verify_arxiv(arxiv_id)
                if arxiv_result["valid"]:
                    results["arxiv_valid"] += 1
                    method_result["arxiv_title"] = arxiv_result["title"]
                else:
                    results["arxiv_invalid"].append({
                        "domain": domain_name,
                        "method": m["name"],
                        "arxiv_id": arxiv_id,
                        "error": arxiv_result.get("error"),
                    })
                    method_result["issues"].append(f"arXiv {arxiv_id}: {arxiv_result.get('error')}")
                time.sleep(3)  # arXiv rate limit (3 sec between requests)

            # Verify GitHub
            code = m.get("code")
            if code and "/" in str(code):
                results["github_checked"] += 1
                gh_result = verify_github(code, token)
                if gh_result["valid"]:
                    results["github_valid"] += 1
                    # Check star count discrepancy
                    yaml_stars = m.get("stars")
                    api_stars = gh_result.get("stars")
                    if yaml_stars and api_stars and abs(yaml_stars - api_stars) > api_stars * 0.3:
                        method_result["issues"].append(
                            f"Stars mismatch: YAML={yaml_stars}, API={api_stars}"
                        )
                else:
                    results["github_invalid"].append({
                        "domain": domain_name,
                        "method": m["name"],
                        "repo": code,
                        "error": gh_result.get("error"),
                    })
                    method_result["issues"].append(f"GitHub {code}: {gh_result.get('error')}")
                time.sleep(0.3)

            if method_result["issues"]:
                domain_results["methods"].append(method_result)

            if quick and results["arxiv_checked"] >= 20:
                break

        if domain_results["methods"]:
            results["domains"][domain_name] = domain_results

    return results


def print_report(results: dict) -> None:
    print(f"\n{'='*60}")
    print(f"VERIFICATION REPORT")
    print(f"{'='*60}")
    print(f"Total methods: {results['total_methods']}")
    print(f"\narXiv: {results['arxiv_valid']}/{results['arxiv_checked']} valid")
    if results["arxiv_invalid"]:
        print(f"  INVALID arXiv IDs ({len(results['arxiv_invalid'])}):")
        for item in results["arxiv_invalid"]:
            print(f"    [{item['domain']}] {item['method']}: {item['arxiv_id']} ({item['error']})")

    print(f"\nGitHub: {results['github_valid']}/{results['github_checked']} valid")
    if results["github_invalid"]:
        print(f"  INVALID repos ({len(results['github_invalid'])}):")
        for item in results["github_invalid"]:
            print(f"    [{item['domain']}] {item['method']}: {item['repo']} ({item['error']})")

    # Issues per domain
    if results["domains"]:
        print(f"\nIssues by domain:")
        for dname, ddata in results["domains"].items():
            issues = [i for m in ddata["methods"] for i in m["issues"]]
            if issues:
                print(f"  {dname}: {len(issues)} issues")
                for m in ddata["methods"]:
                    for issue in m["issues"]:
                        print(f"    {m['name']}: {issue}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Verify domain YAML data against APIs")
    parser.add_argument("--dir", default=str(DOMAINS_DIR), help="Domains directory")
    parser.add_argument("--quick", action="store_true", help="Quick check (first 20 arXiv only)")
    parser.add_argument("--domain", help="Check only this domain (filename without .yaml)")
    parser.add_argument("--save", action="store_true", help="Save report to JSON")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[WARN] GITHUB_TOKEN not set — GitHub rate limit will be low")

    domains_dir = Path(args.dir)
    if args.domain:
        # Temporarily rename to check single domain
        single = domains_dir / f"{args.domain}.yaml"
        if not single.exists():
            print(f"[ERROR] {single} not found")
            sys.exit(1)

    print("Verifying data against external APIs...")
    results = verify_all(domains_dir, token, args.quick)
    print_report(results)

    if args.save:
        REPORT_PATH.parent.mkdir(exist_ok=True)
        with REPORT_PATH.open("w") as f:
            json.dump(results, f, indent=2)
        print(f"\nReport saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
