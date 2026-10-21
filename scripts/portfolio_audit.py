#!/usr/bin/env python3
"""Read-only GitHub portfolio inventory and release-readiness triage.

Requires Python 3.11+. Uses only stdlib. Never exposes secret values or writes
to repositories. A separate release process must verify builds and deployments.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
OWNER = os.getenv("PORTFOLIO_OWNER", "belentani7")
TOKEN = os.getenv("PORTFOLIO_AUDIT_TOKEN")
SNAPSHOT = pathlib.Path(__file__).resolve().parent.parent / "data" / "portfolio-repositories-2026-10-21.json"
SCOPE = "authenticated_live_github" if TOKEN else "historical_snapshot_unverified"
OUT = pathlib.Path(os.getenv("AUDIT_OUTPUT", "artifacts/portfolio"))
MAX_REPOS = max(1, min(int(os.getenv("MAX_REPOS", "1000")), 2000))
MAX_CONTENT_CHECKS = max(0, min(int(os.getenv("MAX_CONTENT_CHECKS", "120")), 2000))
TIMEOUT = 20
REQUIRED = ("README.md", "LICENSE", ".gitignore")
CATEGORY_HINTS = {
    "education": ("school", "lingua", "course", "learn", "educ", "moodle", "manos"),
    "music_art": ("judas", "music", "duck", "belentani-experience", "artist", "michelle", "natalia"),
    "ai_tools": ("cv-ai", "agent", "ai-", "noia", "aion", "lab"),
}
def api(path: str):
    url = API + path
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "belentani-portfolio-auditor/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
        **({"Authorization": "Bearer " + TOKEN} if TOKEN else {}),
    })
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code in (401, 403, 429):
            raise RuntimeError(f"GitHub API HTTP {exc.code} at {path}; check token scopes/rate limit") from exc
        raise

def repo_pages():
    if not TOKEN:
        # The workflow GITHUB_TOKEN is scoped to this one repository.
        # The checked-in historical snapshot is private and is never live evidence.
        snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        if snapshot.get("total") != len(snapshot.get("repositories", [])):
            raise RuntimeError("Historical portfolio snapshot count mismatch")
        return [
            {
                **repo, "owner": {"login": OWNER}, "fork": False,
                "homepage": None, "description": None,
                "updated_at": None, "pushed_at": None,
            }
            for repo in snapshot["repositories"][:MAX_REPOS]
        ]
    repos = []
    for page in range(1, (MAX_REPOS + 99)//100 + 1):
        endpoint = ("/user/repos?affiliation=owner&visibility=all&sort=updated&per_page=100"
                    if TOKEN else f"/users/{urllib.parse.quote(OWNER)}/repos?type=owner&sort=updated&per_page=100")
        batch = api(endpoint + f"&page={page}")
        if not isinstance(batch, list):
            raise RuntimeError("GitHub returned unexpected repository listing")
        repos.extend(x for x in batch if x.get("owner", {}).get("login", "").lower() == OWNER.lower())
        if len(batch) < 100 or len(repos) >= MAX_REPOS:
            break
        time.sleep(0.12)
    return repos[:MAX_REPOS]

def category(name):
    n = name.lower()
    for label, hints in CATEGORY_HINTS.items():
        if any(v in n for v in hints):
            return label
    return "unclassified"

def inspect(repo, do_contents):
    name = repo["name"]
    status = "archived" if repo.get("archived") else "needs_review"
    result = {
        "name": name, "full_name": repo["full_name"], "private": repo.get("private", True),
        "archived": repo.get("archived", False), "fork": repo.get("fork", False),
        "updated_at": repo.get("updated_at"), "pushed_at": repo.get("pushed_at"),
        "default_branch": repo.get("default_branch"), "homepage": repo.get("homepage"),
        "description": repo.get("description"), "category_hint": category(name),
        "status": status, "checks": {}, "missing": [],
        "release_authorized": False, "deployed_verified": False,
        "purpose_verified": False, "content_verified": False,
    }
    if not TOKEN:
        result["checks"]["content_audit"] = "historical_snapshot_only"
        result["status"] = "archived_in_snapshot" if repo.get("archived") else "unverified_snapshot"
        return result
    if not do_contents or repo.get("archived"):
        result["checks"]["content_audit"] = "not_scanned"
        return result
    path = "/repos/" + urllib.parse.quote(OWNER) + "/" + urllib.parse.quote(name) + "/contents"
    listing = api(path)
    if not isinstance(listing, list):
        result["checks"]["content_audit"] = "unavailable"
        return result
    names = {item["name"] for item in listing}
    result["checks"]["root_files"] = sorted(names)
    result["missing"] = [f for f in REQUIRED if f not in names]
    result["checks"]["has_tests_or_ci"] = bool(names & {"tests", "test", "__tests__", ".github", "pytest.ini"})
    result["checks"]["has_homepage_entry"] = bool(names & {"index.html", "app", "src", "pages", "index.tsx"})
    result["checks"]["has_manifest"] = bool(names & {"package.json", "pyproject.toml", "pom.xml", "Cargo.toml", "go.mod", "composer.json"})
    result["status"] = "manual_product_validation_required"
    return result

def main():
    if not TOKEN:
        print("SNAPSHOT MODE: no PORTFOLIO_AUDIT_TOKEN; no live cross-repo inspection", file=sys.stderr)
    repos = repo_pages()
    results = []
    # Rotate the scanned batch. GitHub-hosted runs have no durable filesystem,
    # so default to a deterministic daily rotation; Linux can persist a cursor.
    total = len(repos)
    default_offset = int(dt.datetime.now(dt.timezone.utc).timestamp() // (4 * 3600)) * MAX_CONTENT_CHECKS
    scan_offset = int(os.getenv("AUDIT_SCAN_OFFSET", str(default_offset)))
    checked = {(scan_offset + j) % total
               for j in range(min(total, MAX_CONTENT_CHECKS))} if total and TOKEN else set()
    for i, r in enumerate(repos):
        try:
            results.append(inspect(r, i in checked))
        except Exception as exc:
            results.append({"name": r.get("name"), "full_name": r.get("full_name"),
                            "status": "inspection_error", "error": str(exc),
                            "release_authorized": False, "deployed_verified": False})
        if i % 25 == 0:
            print(f"Inspected {i + 1}/{len(repos)}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    payload = {"generated_at": now, "owner": OWNER, "total_visible": len(results),
               "contents_scanned": len(checked), "scan_offset": scan_offset,
               "inventory_scope": SCOPE,
               "live_authenticated": bool(TOKEN),
               "expected_snapshot_total": 490,
               "policy": "Inventory is evidence, not product or release certification",
               "repositories": results}
    (OUT / "inventory.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    groups = {}
    for item in results:
        groups[item["status"]] = groups.get(item["status"], 0) + 1
    lines = ["# Portfolio release-readiness inventory", "",
             f"Generated (UTC): {now}", f"Visible repositories: **{len(results)}**",
             f"Root-level inspection attempts: **{len(checked)}** (offset: {scan_offset})",
             f"Scope: **{SCOPE}**. Snapshot rows are NOT live source-code checks.",
             "", "## Audit state", ""]
    lines += [f"- {key}: {value}" for key, value in sorted(groups.items())]
    lines += ["", "## Release policy", "",
              "No repository is declared complete or ready to publish by this script.",
              "Root-file presence is NOT proof of working features, real course content,",
              "security, legal eligibility, SEO discoverability, successful tests,",
              "or reachable production URLs.", "",
              "## Repository triage", "",
              "| Repository | Hint | State | Missing root basics |",
              "|---|---|---|---|"]
    for item in results:
        nm = str(item.get("name", "")).replace("|", "\\|")
        lines.append(f"| {nm} | {item.get('category_hint','-')} | {item['status']} | {', '.join(item.get('missing',[])) or '-'} |")
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT / 'inventory.json'} and {OUT / 'report.md'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
