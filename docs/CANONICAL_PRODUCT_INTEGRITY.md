# Factory guard: canonical product integrity — 2026-10-22

This is an executable **regression guard**, not another product, roadmap or
"100% complete" claim. It exists because several unrelated repositories were
given the same `Professional project template` manifest even though their
original applications use Java, Next.js, Vite monorepos, Python or static HTML.

## Checks implemented

`scripts/product-identity.mjs` contains an **explicit, conservative allowlist**
of 12 existing repository identities (not automatic identity inference).
For each repo it evaluates root source markers, expected runtime commands,
missing manifests, generic boilerplate descriptions and cross-stack Vite
scaffolds. It returns one of:

- `blocked_identity_regression`: an actual manifest/root contract is violated.
  Do **not** merge, deploy, or declare the project complete.
- `manual_product_validation_required`: basic identity is consistent; it
  still requires real application tests, design, lessons, data, security and
  deployment checks. **Not** a release approval.
- `unclassified`: the repo has no agreed canonical fingerprint.
  Inspect its genuine history and purpose; do not invent a product identity.
- `inspection_unverified`: access or reading failed. It is not a pass.

An unrecognized repo is never dropped, "made into a website", or
automatically merged with a similarly named product.

## Workstation use (requires Node 22+, no npm install)

```bash
node --test tests/product-identity.test.mjs tests/scan-canonical-portfolio.test.mjs
node scripts/check-product-identity.mjs belentani7/ManosAbiertas /path/to/its/checkout
node scripts/check-product-identity.mjs belentani7/NOIACORE /path/to/its/checkout
```

Exit code 1 = blocked regression. Exit code 2 = unknown or unreadable checkout.
Exit code 0 = no **known manifest regression**; not evidence of completeness,
CI success, production readiness or Google discoverability.

## Autonomous read-only GitHub scan

`.github/workflows/product-identity.yml` runs scheduled read-only checks
daily at 06:17 UTC *after the workflow is reviewed and merged on main*.
The workflow also runs contract tests on its own PRs. It uses a scoped
`PORTFOLIO_AUDIT_TOKEN` secret with read-only Contents/Metadata access to the
**12 authorized repositories**. Do not use a broad write token, reuse
deployment keys, paste credentials in README, or leak private inventories
to GitHub Pages/Vercel.

Without a suitable secret, the CLI records `unverified_no_private_token`
and exits nonzero instead of fabricating fresh results. The private
`product-identity.json` report is retained as a GitHub Actions artifact for
seven days; do not publish this file on a public domain.

The project currently also has GitHub-hosted runner failures. Until a
successful scheduled or manual run appears in Actions, the scan is **code
prepared, not an operating service**.

## Recovering authentic applications

1. Confirm exact GitHub repository ID and canonical identity, purpose and
   previous legitimate commit in its own history. Michelle Relayze and
   Natalia Marinho remain strictly distinct identities and websites.
2. Diff the original `package.json`, Java `pom.xml`, Python project config,
   CI, lockfile and application routes against the proposed restore branch.
3. Recover only genuinely intended files; do not delete lessons, artist
   content, education curricula, tests or databases to make CI quiet.
4. Run the framework's real lockfile install, typecheck, security and tests,
   browser E2E, accessibility and appropriate data/content acceptance gates.
5. Preview the **exact SHA** privately, inspect server routes and SEO on
   public pages only. Confirm the correct Vercel project and domain; never
   deploy one brand over a similarly named but different product.
6. Merge and promote only after checks actually pass and a rollback exists.

### Existing recovery PRs

- `open-school` PR 46: restore original curricula and Vite build.
- `linguaforge` PR 40: restore its API/Drizzle monorepo build.
- `NOIACORE` PR 19: restore Maven/Spring Boot and Black Water.
- `ManosAbiertas` PR 62: restore Next.js and Prisma.
- `belentani.es` PR 52: restore actual Next.js application.
- `agent-orchestration-machine` PR 14: remove unrelated generic Vite scaffold.

These are **separate reviews**, not an automatic mass merge. The guard
must never perform destructive repository operations or auto-release software.

This code only checks deliberately limited metadata. It does not contact
Google, deploy to Vercel, check course lessons, establish identity ownership
or certify a product as complete.
