# BELENTANI Factory Control · Private Local Console

A complete, usable **offline-first UI** for the existing portfolio inventory.
This is a local operator console, **not** a public site and **not** a release
certificate. It does not run agents, deploy projects or alter GitHub repos.

## Run on Linux, Windows or macOS

From the repository root, with Python 3.11+:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory site
```

Open `http://127.0.0.1:8765/`. The server binds only to loopback. Never
expose this interface on `0.0.0.0`, a public host or GitHub Pages.

Select **Importar inventario**, then choose
`data/portfolio-repositories-2026-10-21.json` (historical 490-entry
snapshot), or `artifacts/portfolio/inventory.json` from an authenticated
Linux audit. The local browser reads JSON with the File API; it performs no
`fetch()` request, cloud upload, analytics or browser storage.

## Real delivered functionality

- Premium monochrome visual identity with responsive layout, a homepage,
  a working search and filtered repository list, and a detail inspector.
- Historical vs live-audit scope appears explicitly, with exact counts.
- Three status/category/sort filters and paginated 20-row navigation.
- Accessible labels, semantic main and navigation areas, skip link,
  keyboard-operable import control, visible focus and reduced-motion support.
- Strong default CSP (no network connections or third-party scripts),
  `noindex` and no automatic loading of private portfolio data.
- Invalid, duplicate, oversized and path-like imported records are rejected.
- The UI does **not** declare a repo complete, does **not** display an
  unverified count as a finished release, and never changes source repos.

## Evidence and checks

```bash
node --test site/portfolio.test.mjs
node --check site/portfolio.mjs
node --check site/app.mjs
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Node.js 22+ is recommended. The CI workflow includes these checks, but the
current GitHub Actions runner incident is external to this code; passing a
local static check does not imply browser, security or usability signoff.
A browser E2E test is required before a production-quality console claim.

## Privacy boundary

- Keep `data/` and `artifacts/` private; do not commit them to a public
  repository or ship them as a website.
- Use `PORTFOLIO_AUDIT_TOKEN` only as a protected Actions secret for the
  separate Python CLI; **never** place tokens in the browser console.
- `live_authenticated` is merely a declaration inside the imported file;
  verify provenance from a trusted run before relying on it.
- Private HTML is for an authorized operator at `localhost`; robots/noindex
  are extra safeguards and **are not** substitutes for authentication.
- To discard data, click **Limpiar datos** or close the tab. No persistence.

This console is one part of the complete existing `agent-orchestration-machine`
product and follows `AGENTS.md` and `docs/RELEASE_QUALITY_2026.md`.
