# Autonomous portfolio inventory (phase 1)

This is **a scheduled read-only inventory, not an autonomous production deployment**.

## Setup
1. Add repository Actions secret `PORTFOLIO_AUDIT_TOKEN` with read-only access to the owner's intended **private repositories**. Do not use a write/admin token. The default `GITHUB_TOKEN` can usually read only this workflow's repository, not the private portfolio.
2. Enable GitHub Actions and scheduled workflows for this repository.
3. Trigger **Actions → Portfolio inventory and readiness → Run workflow**.
4. Download the `portfolio-audit` artifact containing `inventory.json` and `report.md`. GitHub-hosted runners are ephemeral. The generated artifact is retained for 14 days.

## Safety gates
- No public/private visibility changes, no new repositories, no deletes or merges.
- No deployments, no paid infrastructure provisioning, no AI-model API billing.
- No repo receives `complete` or `release_authorized` from file-name checks.
- Human or independently verified project-specific acceptance criteria required before publishing.
- Token receives **read-only** repo access, is stored in GitHub Actions secrets, and is never printed.

## Next stage (not implemented)
Persist backlog and job leases in a database or GitHub Issues; attach workers on persistent Linux via a restricted GitHub App; run reproducible build/unit/E2E/accessibility/secret scans; deploy to preview; smoke test; promote after verified release gates. A scheduled inventory is not a continuously running worker.

## Product completeness
Define a signed-off manifest for each canonical project: audience, proposition, promised features, genuine content (for educational sites: course structure, full lessons, exercises and assessments), homepage and flows, keyboard/mobile accessibility, privacy policy where appropriate, security, SEO and machine-readable structured data, tests, operational telemetry, real deployment URL, rollback. Do not label incomplete projects complete.
