# Portfolio Autonomous Linux Runner — Phase 1

This repository is the **canonical orchestration engine**. On merge to `main`,
GitHub Actions provisions an ephemeral Ubuntu 24.04 worker every four hours at
minute 23 UTC (subject to runner availability, GitHub billing limits and schedule
delay). It is not a permanently running Linux VPS, and it does not autonomously
ship unreviewed production software.

## Current functional scope
- Read-only portfolio inventory of all currently accessible repositories.
- Private historical snapshot from 21 October 2026: 490 repository identities
  (281 active, 209 archived). Snapshot is historical evidence, **not** a live check.
- Rotating root-directory checks of up to 120 repositories per authenticated
  run; report `manual_product_validation_required` rather than `complete`.
- Unit tests first, then `inventory.json` and `report.md` stored only in
  private GitHub Actions artifacts for 14 days.

## Credentials and activation
1. Ensure Actions runners are enabled, available and within billing/quota.
2. Set a least-privilege repository Action secret `PORTFOLIO_AUDIT_TOKEN`,
   authorized to **read metadata and contents** of the intended private repos.
   Scope it to those repositories; never paste the token in code or chat.
3. Merge the reviewed workflow on `main`; scheduling works **only** on
   the default branch. Use **Actions → Portfolio inventory and readiness →
   Run workflow** to check a first run.
4. Inspect the artifact's `inventory_scope`. It must be
   `authenticated_live_github` before treating its data as up to date.
   Without the secret, scope is `historical_snapshot_unverified`: the runner
   still inventories the 490 remembered entries but makes **zero** cross-repo
   content requests.
5. Before releasing any product, follow `docs/RELEASE_QUALITY_2026.md`.

## Specialist responsibilities
`AGENTS.md` defines product, UX, content, security, SEO, QA and release
specialists. These are execution roles and future bounded agents, **not seven
already-running AI models**. To enable model-generated PRs, configure a
supported engine using GitHub Agentic Workflows (`gh-aw`) or equivalent,
review the compiled workflow, install its exact required credentials and only
allow scoped draft pull requests. Do not grant agents direct production secrets.

## Publication policy
A release must have a complete product-specific specification and proof:
real homepage where appropriate, real promised content, successful tests,
accessible UI, valid SEO only for public content, live preview, tested
deployment/rollback, verified production URL. A successful build is not enough.

No scheduled worker is permitted to create/delete repositories, change their
visibility, force push, silently merge PRs, purchase services or publish private
inventory. The audit only **triages**; it does not certify products complete.

## Linux cost controls
At most one concurrent inventory job, six scheduled starts/day, up to 12
minutes each, with an explicit timeout. Confirm Actions quota before relying on
it; high load can delay scheduled jobs, and quotas can block runners.
Avoid paid Hugging Face scheduled compute until a defined budget exists.

## Evidence references
- GitHub scheduled workflows: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- GitHub token scope: https://docs.github.com/en/actions/concepts/security/github_token
- GitHub Agentic Workflows: https://github.com/github/gh-aw
