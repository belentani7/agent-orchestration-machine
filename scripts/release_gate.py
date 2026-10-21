#!/usr/bin/env python3
"""Fail-closed, SHA-pinned GitHub pull-request release gate.

Read-only by default. Only 'merge' with explicit expected SHA and required checks
can write, and never force pushes, creates repositories, changes visibility or
claims that a deployment exists. Python 3.11+, standard library only.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

API = "https://api.github.com"
GENERIC_DESCRIPTION = "professional project template"
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
SHA = re.compile(r"^[0-9a-f]{40}$")


class GateError(RuntimeError):
    """A release must stop, not proceed with incomplete evidence."""


class ApiError(GateError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class Candidate:
    repository: str
    number: int
    head_sha: str
    base_sha: str
    checks: tuple[str, ...]
    ahead_by: int
    changed_files: tuple[str, ...]


def _path(part: str) -> str:
    if not SAFE_NAME.fullmatch(part):
        raise GateError(f"Invalid GitHub repository identifier: {part!r}")
    return urllib.parse.quote(part, safe="")


class GitHub:
    def __init__(self, token: str):
        if not token:
            raise GateError("GITHUB_TOKEN is required; never run against unverified fixtures")
        self._token = token

    def call(self, path: str, method: str = "GET", payload: dict[str, Any] | None = None):
        if not path.startswith("/repos/"):
            raise GateError("Only GitHub repository endpoints may be called")
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "belentani-sha-release-gate/1.0",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(API + path, method=method, headers=headers, data=body)
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            raise ApiError(exc.code, f"GitHub HTTP {exc.code} for {method} {path}; release stopped") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise GateError(f"GitHub API unavailable for {method} {path}; release stopped") from exc


def _pages(client: GitHub, path: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in range(1, 21):
        data = client.call(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
        if not isinstance(data, list):
            raise GateError("Unexpected paginated response; release stopped")
        items.extend(data)
        if len(data) < 100:
            return items
    raise GateError("More than 2000 entries; pagination incomplete; release stopped")


def verify(client: GitHub, repository: str, number: int, expected_sha: str, required: list[str]) -> Candidate:
    """Raise on any missing, stale, failing or unverifiable evidence."""
    parts = repository.split("/")
    if len(parts) != 2:
        raise GateError("Pass exactly owner/repository")
    owner, name = (_path(p) for p in parts)
    if number < 1 or not SHA.fullmatch(expected_sha):
        raise GateError("A PR number and full 40-character expected head SHA are required")
    if not required or len(set(required)) != len(required):
        raise GateError("Specify at least one unique real required check name")
    prefix = f"/repos/{owner}/{name}"
    pr = client.call(f"{prefix}/pulls/{number}")
    if pr.get("state") != "open" or pr.get("draft") or pr.get("merged"):
        raise GateError("PR is not open, reviewed and ready (or is a draft)")
    if pr.get("head", {}).get("sha") != expected_sha:
        raise GateError("PR head moved; expected SHA does not match (TOCTOU protection)")
    if pr.get("head", {}).get("repo", {}).get("full_name", "").lower() != repository.lower():
        raise GateError("Cross-repository PR; do not mix products")
    if pr.get("base", {}).get("ref") != "main":
        raise GateError("PR must target this product's main branch")
    if pr.get("mergeable") is not True or pr.get("mergeable_state") in ("dirty", "blocked", "unknown"):
        raise GateError("PR mergeability is not confirmed")

    compare = client.call(f"{prefix}/compare/main...{expected_sha}")
    if compare.get("status") != "ahead" or compare.get("behind_by") != 0:
        raise GateError("Branch diverged from main; reconcile and re-run complete gates")
    if compare.get("ahead_by", 0) < 1:
        raise GateError("No release commits exist")
    base_sha = pr.get("base", {}).get("sha", "")
    if compare.get("base_commit", {}).get("sha") != base_sha:
        raise GateError("Target branch moved since comparison; re-run gates")

    files = _pages(client, f"{prefix}/pulls/{number}/files")
    if not files:
        raise GateError("No files in PR")
    if any(f.get("status") in ("removed", "renamed") for f in files):
        raise GateError("Deletion/rename requires separate human review; no automatic merge")
    filenames = tuple(str(f.get("filename", "")) for f in files)
    try:
        pkg = client.call(f"{prefix}/contents/package.json?ref={expected_sha}")
    except ApiError as exc:
        if exc.status != 404:
            raise
        pkg = None  # A non-Node product can have no package.json.
    if pkg and pkg.get("content"):
        try:
            manifest = json.loads(base64.b64decode(pkg["content"]).decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise GateError("Invalid package.json in candidate") from exc
        if str(manifest.get("description", "")).strip().lower() == GENERIC_DESCRIPTION:
            raise GateError("Generic scaffold manifest; original product not restored")

    check_response = client.call(f"{prefix}/commits/{expected_sha}/check-runs?per_page=100")
    if not isinstance(check_response, dict) or "check_runs" not in check_response:
        raise GateError("GitHub check results unavailable")
    checks = check_response["check_runs"]
    if check_response.get("total_count", 0) > len(checks):
        raise GateError("Check results truncated; cannot certify all checks")
    checks_by_name: dict[str, list[dict[str, Any]]] = {}
    for check in checks:
        checks_by_name.setdefault(str(check.get("name", "")), []).append(check)
        if check.get("status") != "completed" or check.get("conclusion") not in ("success", "skipped", "neutral"):
            raise GateError(f"Failed or unfinished check: {check.get('name')}")
    status = client.call(f"{prefix}/commits/{expected_sha}/status")
    legacy = status.get("statuses", [])
    if any(x.get("state") != "success" for x in legacy):
        raise GateError("A deployment/legacy status is not successful")
    for check_name in required:
        matching = checks_by_name.get(check_name, [])
        if len(matching) != 1 or matching[0].get("conclusion") != "success":
            raise GateError(f"Required check missing, duplicate, skipped or failed: {check_name}")
    if not checks and not legacy:
        raise GateError("No independent checks ran; refusal is intentional")
    return Candidate(repository, number, expected_sha, base_sha, tuple(required), compare["ahead_by"], filenames)


def merge(client: GitHub, candidate: Candidate) -> dict[str, Any]:
    """One optimistic-concurrency-protected squash merge. Never deploys unverified code."""
    owner, name = (_path(p) for p in candidate.repository.split("/"))
    current_base = client.call(f"/repos/{owner}/{name}/git/ref/heads/main")
    if current_base.get("object", {}).get("sha") != candidate.base_sha:
        raise GateError("main changed after verification; re-run all checks")
    path = f"/repos/{owner}/{name}/pulls/{candidate.number}/merge"
    result = client.call(path, method="PUT", payload={
        "sha": candidate.head_sha,
        "merge_method": "squash",
        "commit_title": f"release: integrate verified PR #{candidate.number}",
    })
    if result.get("merged") is not True or not SHA.fullmatch(str(result.get("sha", ""))):
        raise GateError("GitHub did not confirm merge; do not claim delivery")
    return {"merged": True, "commit_sha": result["sha"], "repository": candidate.repository,
            "production_verified": False, "production_deployed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="Exact existing owner/repo")
    parser.add_argument("pr", type=int, help="Exact PR number")
    parser.add_argument("--expected-head", required=True, help="Full 40-character SHA (not branch name)")
    parser.add_argument("--require-check", action="append", required=True, help="Exact check-run name; repeat")
    parser.add_argument("--merge", action="store_true", help="Explicitly authorize SHA-pinned squash merge")
    args = parser.parse_args(argv)
    try:
        gh = GitHub(os.getenv("GITHUB_TOKEN", ""))
        candidate = verify(gh, args.repository, args.pr, args.expected_head, args.require_check)
        result = {"ready": True, "repository": candidate.repository, "pr": candidate.number,
                  "head_sha": candidate.head_sha, "base_sha": candidate.base_sha,
                  "required_checks_passed": list(candidate.checks), "changed_files": candidate.changed_files,
                  "mode": "merge" if args.merge else "read_only", "production_verified": False}
        if args.merge:
            result.update(merge(gh, candidate))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except GateError as exc:
        print(json.dumps({"ready": False, "merged": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
