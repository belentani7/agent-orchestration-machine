# Product-release quality contract — 2026

**Rule:** software is finished when the promised experience works end-to-end for the
intended audience in production, with genuine content and verified maintenance.
A deployed shell, pretty mockup, passing build, or automated output does not qualify.

## 1. Identity and scope (all projects)
- `PRODUCT.md`: purpose, target audience, value, owner, exact canonical repository,
  dependencies, features promised to users, acceptance tests and out-of-scope.
- Each product must have a coherent architecture, explanatory README, license or
  explicit proprietary status, reproducible commands and a current operating guide.
- No unrelated apps inside one repo unless it is an intentionally documented monorepo.
- No fake endorsements, fake usage counters, fake certifications or placeholder pages.

## 2. Usable premium experience (web, platform, service)
- A real landing/homepage describing what it does, for whom, with an unmistakable CTA;
  coherent design tokens, type scale, spacing, real imagery and loading states.
- All advertised navigation destinations render meaningful pages, including error,
  empty, offline and authentication states where applicable.
- Mobile portrait, desktop and wide screens; responsive typography and touch targets;
  keyboard operability, visible focus, reduced motion, semantic landmarks and labels.
- Test accessibility against WCAG 2.2 AA where applicable, not only automated scores.
- Performance budgets and optimization driven by measurable Core Web Vitals, not animation hype.

## 3. Real product outcomes by category
| Type | Non-negotiable delivered substance |
|---|---|
| Educational site/course | Real curriculum, complete modules, full lessons, examples, practice, feedback, assessments, progress persistence and accessible learning paths; legal guidance clearly sourced and dated |
| Artist/music site | Artist identity, valid biography, real discography/releases, working media where licensed, press kit, contact information, accessible event content |
| AI tool | Working inference/use case; graceful no-key mode if promised; input validation, usage limits, data retention disclosure, meaningful output and fallbacks |
| SaaS/admin | Real dashboard, authenticated roles, tenant isolation, usable create/edit flows, durable storage, migrations, errors, account lifecycle and monitoring |
| Portfolio | Concrete experience, verifiable projects/outcomes, real case studies and contact path; no invented metrics |
| Headless library/CLI | Complete documented API and CLI entrypoint with examples, tests, versioned artifacts; **do not fake a website if a UI isn't part of its product promise** |

## 4. Safety, privacy, supply chain
- Least privilege, deny-by-default authorization, safe handling of PII, no production
  credentials in frontend, CSRF/CORS/session policy as appropriate.
- Use OWASP ASVS 5.0.0 applicable controls, documented threat model, security headers,
  input bounds, rate limits, dependency audits, lockfiles and secret scanning.
- External model/agent calls limited by explicit budgets; untrusted content is data,
  never privileged instructions; use allowlists for actions and human oversight for
  irreversible operations.
- Backup/restore drills and rollback for durable user data.

## 5. Google and other discoverability (only intended PUBLIC web pages)
- Public 200-response pages have original indexable content and crawlable `<a href>`
  links; private/staging/admin pages use appropriate authentication or `noindex`.
- Correct page titles, meta descriptions, accessible heading structure, one canonical
  URL per page, Open Graph images that resolve, sitemap.xml and robots.txt policies.
- JSON-LD matches REAL content using appropriate Schema.org types (Organization,
  Person, WebSite, Course, SoftwareApplication, MusicGroup, MusicAlbum etc).
- Prefer SSR/static HTML for critical content; do not require client JS to reveal
  the core promise. Test rendered pages with Google's URL Inspection/Rich Results tools.
- Verify domain ownership/search indexing separately: metadata cannot guarantee ranking.

## 6. Release evidence and operational readiness
- CI: exact pinned dependency install, lint/format, type checking, unit tests,
  integration tests and a real build; security and artifact provenance checks.
- E2E: representative critical user journey with browser and accessibility testing,
  including authentication/data persistence where applicable.
- Deployment: preview from known commit SHA, smoke check public assets and endpoints,
  no secret leakage, production publication, monitoring and rollback.
- Review: only label COMPLETE when evidence links, tested dates, reviewer and
  production URL are recorded in `RELEASE.md`; use BLOCKED otherwise.
- If CI fails before getting a runner, record INFRASTRUCTURE_BLOCKED. A successful
  Vercel build is not evidence that security or end-to-end tests succeeded.

## 7. Autonomous delivery policy
- Work on existing authorized repositories; propose one bounded, reviewed PR per
  meaningful change with commands and evidence; avoid unbounded self-modification.
- No merging or promoting when any required gate is failing, skipped or unverified.
- Product/content sign-off is necessary: automated heuristics can flag missing
  evidence, never certify completeness.
- GitHub-hosted Linux jobs are **ephemeral** and scheduled runs may be delayed.
  They are not a permanent server. A persistent queue + authenticated workers are
  separate infrastructure with monitoring and cost controls.

References (official):
- Google Search Central JavaScript SEO: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- Google canonicalization: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- OWASP ASVS 5.0.0: https://asvs.owasp.org/
- GitHub Agentic Workflows: https://github.com/github/gh-aw
- GitHub GITHUB_TOKEN isolation: https://docs.github.com/en/actions/concepts/security/github_token
