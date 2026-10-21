# SHA-pinned release gate — operational runbook

This module lives in **the existing canonical repository**, `agent-orchestration-machine`.
It does not create a new project, run an LLM, fabricate passing tests or deploy blindly.

## Local prerequisites

- Python 3.11+; no third-party dependencies.
- A least-privilege GitHub token authorized for the **specific target repository**.
- `GITHUB_TOKEN` set securely in your shell/runner environment; never commit it.
- The target PR's **actual, full SHA** and the exact names of the test/build checks
  required for that product. Do not infer success from a README or deployment URL.

## Inspect before integrating

```bash
export GITHUB_TOKEN=...  # retrieve securely; do not paste into tickets/logs
python scripts/release_gate.py belentani7/heyduck 10 \
  --expected-head 275950b7d22d83af8545981f04ccafcbb69147e0 \
  --require-check "Media, data and website contract" \
  --require-check "Analyze (javascript-typescript)"
```

The command above **does not merge**. It is expected to fail while current CI is failing.
The check names are examples observed on this repository, not a declaration
that these checks cover every frontend, security, product and content requirement.

Only after required checks are passing on that **same SHA**, a human has verified
the full promised product and preview, and the proposed release is acceptable,
rerun the same command with `--merge`.

## Safety rules enforced

- `main` is the only merge target; cross-repository PRs and all drafts are rejected.
- Branch must be strictly ahead of the current `main` (no unintegrated base commits).
- Full head SHA is pinned in the merge call. The base SHA is checked again immediately
  before the write. GitHub's merge API does **not** support an atomic base-SHA compare,
  so use protected branches with required checks for an additional concurrency guard.
- Any failing, incomplete, unknown, duplicate-required, or missing required check
  blocks the merge. Any non-successful legacy deployment status also blocks it.
- Generic `Professional project template` manifests are blocked. Missing
  `package.json` is tolerated only if GitHub explicitly returns HTTP 404 (non-Node).
- PRs removing/renaming files stop for manual review, including legitimate removals.
- No force-push, repo creation, visibility change, secret readout, payment, DNS write,
  Vercel production promotion, database migration or deletion is performed.
- A successful squash merge is reported as **merged**, never as **deployed** or
  **production verified**. Verify the new production SHA and routes separately.

## Automated testing

```bash
python -m unittest discover -s tests -p 'test_release_gate.py' -v
python -m py_compile scripts/release_gate.py
```

The tests use an in-memory fake GitHub transport. They do not touch any user repo
or cloud project. The existing repository CI test-discovery step also runs them.

## Known blockers (22 October 2026)

- The GitHub Actions checks on multiple product PRs are failing; runner logs may
  be unavailable. This tool deliberately refuses to release such branches.
- Vercel denied the authenticated Open School preview deployment request (HTTP 403).
  A historical READY preview is not proof that the exact current SHA passes.
- Remote Desktop Commander has no connected device; this CLI must be run by an
  authorized runner with the target GitHub token.

Treat this tool as one release-safety component, **not** the full multi-product
architecture, content QA, deployment provider, or security certification.
