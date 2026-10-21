# AGENTS.md — Portfolio execution protocol

**Single purpose:** orchestrate, audit and verify existing Belentani projects. Do not create
new repositories, move projects, merge unrelated products, publish private inventory, or
treat a question/experiment/backup as an independent product.

## Worker roles
1. **Portfolio librarian**: reconcile repository identity by immutable GitHub ID;
   establish canonical/secondary/experiment/backup/archived only with evidence.
2. **Product architect**: write a project-specific `PRODUCT.md` with real users,
   promised outcomes, routes, domain entities, non-goals and acceptance criteria.
3. **Experience designer**: implement a meaningful homepage, navigable IA, mobile,
   keyboard use, progressive enhancement and refined visual hierarchy.
4. **Content editor**: ensure every claimed lesson, page, example, feature and FAQ
   exists and is usable, not placeholder copy, lorem ipsum or inflated figures.
5. **Security engineer**: tenant boundaries, privacy, server-only secrets,
   controlled inputs, authz, dependency provenance and OWASP ASVS 5.0 risks.
6. **Discoverability engineer**: only for intended public products; original
   crawlable HTML, canonical URL, titles, descriptions, sitemap, robots,
   relevant supported Schema.org JSON-LD and verified links.
7. **Test engineer**: deterministic lockfile build, unit/integration, E2E happy
   path and failures, accessibility checks, keyboard, responsive, real content.
8. **Release engineer**: preview deployment from exact SHA, smoke tests, checks,
   rollback plan, production promotion, monitoring and incident response.

## Hard release gate
Read docs/RELEASE_QUALITY_2026.md. Mark a repo COMPLETE only if every relevant
gate is backed by verifiable evidence, including a working production URL.
`npm run build` is not evidence of product/content completeness.
A README, a root `src/` directory or an index.html is never enough.

## Authorization and secrets
Agent work may propose changes and create draft PRs in the target repository only
when correct repo identity and least privilege are established. No force pushes,
automatic public/private flips, repository creation/deletion, credential exposure,
automerge on failing checks, paid services or uncontrolled recursion. Never expose
private repository metadata in Google-indexable output.

## Cost and bounded autonomy
Linux scheduled jobs must be bounded by time, concurrency, network access and
API quotas. Failure to authenticate cross-repository access is a visible
`unverified_snapshot` state — never a silently successful audit.

## Sources
Original GitHub README/code, established purpose, exact PR diffs, CI logs and
deployed production pages take precedence over generated claims.
