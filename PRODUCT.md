# PRODUCT.md — Belentani Factory Control

## Identity

**Product name:** Factory Control, a private operator console and a bounded
automation core for the **existing** Belentani portfolio.

**Canonical repository:** `belentani7/agent-orchestration-machine`.
**Users:** portfolio owner and explicitly authorized maintainers.
**Problem:** hundreds of related, archived, private or experimental repos are
mistaken for independent products; unfinished products are advertised as done.
**Outcome:** inspect the truthful inventory and coordinate evidence-based,
non-destructive delivery of complete existing products.

## Delivered slices

### Local console (this pull request)
- Actual homepage and coherent brand design: black water-like depth, cold white
  light, precise typographic hierarchy, responsive and reduced-motion.
- User imports their own JSON via File API; no upload or background fetch.
- Scope label for historical snapshot vs claimed authenticated read.
- Repository catalog with case-insensitive search, category/status filters,
  sorting and pagination; accessible inspector of current evidence.
- Root metrics read from actual imported data. Never invent completed releases.
- Client-side limits, CSP, robots noindex, no analytics or third-party scripts.
- Documentation and automated Node/Python regression checks.

### Existing orchestration core (not changed here)
- Tenant-scoped task lifecycle, capability policy, audit events, cost budgets.
- Read-only GitHub portfolio inventory on a scheduled ephemeral Linux runner.
- Historical snapshot when a scoped read-only GitHub secret is unavailable.

## Data contract

Accepted JSON:
- Current inventory from `scripts/portfolio_audit.py` with
  `repositories`, `inventory_scope`, `live_authenticated`,
  `total_visible`, `owner`.
- Existing historical `data/portfolio-repositories-2026-10-21.json`
  with `total`, `repositories`, repo IDs/names/archival flags.

Client never accesses a GitHub PAT and does not persist the imported data.
The `live_authenticated` flag is an **imported claim**, not independent proof;
operator must verify source provenance.

## Exclusions

Not a hosted multi-user SaaS, not production hosting, not an autonomous
writing agent, not remote IDE, not a public Google-indexable catalog, and not
an automatic publisher. Existing artist and educational repos remain separate.

## Release acceptance criteria

- [x] Complete source implementation and entrypoint in canonical repo branch.
- [x] Pure local JSON importer with type checks, duplicate detection and limits.
- [x] Responsive homepage, search, filters, pagination, details and zero-data UI.
- [x] Strong client-side isolation, no network calls, no persistence, noindex.
- [x] Test files for logic and static privacy/accessibility properties.
- [ ] GitHub runner actually executes and passes Python and Node tests.
- [ ] Manual desktop + mobile + keyboard E2E verified in a real browser.
- [ ] Privacy review confirms no data leaked from preview/public static build.
- [ ] Reviewer signs off on release; deployment is intentionally PRIVATE.
- [ ] `RELEASE.md` records precise build/test provenance and rollback.

`READY` is not a source-controlled Boolean. A finished product must have
verifiable evidence of all applicable requirements.
