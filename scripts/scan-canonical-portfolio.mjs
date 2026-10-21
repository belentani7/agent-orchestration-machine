#!/usr/bin/env node
/**
 * Authenticated, READ-ONLY cross-repository product integrity report.
 * Only inspects an explicit, existing canonical allowlist; never deploys or
 * modifies any repository. Requires PORTFOLIO_AUDIT_TOKEN, not GITHUB_TOKEN.
 */
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { pathToFileURL } from "node:url";
import { CANONICAL, inspectProductIdentity } from "./product-identity.mjs";

const MAX_CONTENT_BYTES = 512_000;
const REPOSITORIES = Object.keys(CANONICAL).sort();

async function githubJson(fetcher, endpoint, token) {
  const response = await fetcher("https://api.github.com/repos/belentani7/" + endpoint, {
    headers: {
      Authorization: "Bearer " + token,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "belentani-factory-canonical-integrity/1",
    },
    signal: AbortSignal.timeout(20000),
  });
  if (!response.ok) {
    throw new Error("GitHub read request failed: HTTP " + response.status);
  }
  return response.json();
}

export async function scanCanonicalPortfolio({token, fetcher = fetch} = {}) {
  const generatedAt = new Date().toISOString();
  if (typeof token !== "string" || !token.trim()) {
    return {generated_at:generatedAt, scope:"unverified_no_private_token", checked:0,
      expected:REPOSITORIES.length, status:"not_scanned", repositories:[]};
  }
  const reports = [];
  for (const name of REPOSITORIES) {
    try {
      const listing = await githubJson(fetcher, encodeURIComponent(name) + "/contents", token);
      if (!Array.isArray(listing)) throw new Error("GitHub root listing is not an array");
      const names = listing.map(item => item.name);
      let manifest = null;
      if (names.includes("package.json")) {
        const raw = await githubJson(fetcher, encodeURIComponent(name) + "/contents/package.json", token);
        if (raw.encoding !== "base64" || !raw.content || raw.size > MAX_CONTENT_BYTES) {
          throw new Error("Unreadable or oversized package manifest");
        }
        const bytes = Buffer.from(raw.content.replaceAll("\\n",""), "base64");
        if (bytes.length > MAX_CONTENT_BYTES) throw new Error("Oversized decoded package");
        manifest = JSON.parse(bytes.toString("utf8"));
      }
      reports.push(inspectProductIdentity({fullName:"belentani7/" + name,
        rootNames:names, packageJson:manifest}));
    } catch {
      // No raw API errors, repository contents, secrets or tokens in reports.
      reports.push({repository:"belentani7/" + name, kind:CANONICAL[name].kind,
        state:"inspection_unverified", findings:["authentication_or_read_error"],
        releaseAuthorized:false});
    }
  }
  return {
    generated_at: generatedAt,
    scope:"authenticated_github_current_checkout",
    checked:reports.filter(r => r.state !== "inspection_unverified").length,
    attempted:reports.length,
    expected:REPOSITORIES.length,
    status:reports.some(r => r.state === "blocked_identity_regression")
      ? "blocked_regressions_present"
      : reports.some(r => r.state === "inspection_unverified")
      ? "incomplete_unverified" : "manifest_review_required",
    releaseAuthorized:false, repositories:reports,
  };
}
async function cli() {
  const report = await scanCanonicalPortfolio({token:process.env.PORTFOLIO_AUDIT_TOKEN});
  const out = process.env.PRODUCT_IDENTITY_OUTPUT || "artifacts/portfolio/product-identity.json";
  mkdirSync(dirname(out), {recursive:true,mode:0o700});
  writeFileSync(out, JSON.stringify(report, null, 2) + "\n", {mode:0o600});
  const counts = report.repositories.reduce((acc,entry) => {
    acc[entry.state] = (acc[entry.state] || 0) + 1; return acc;
  }, {});
  console.log(JSON.stringify({scope:report.scope,status:report.status,
    expected:report.expected,checked:report.checked,counts,output:out}));
  // Non-zero when incomplete or risky. There is never an auto-release state.
  process.exitCode = report.status === "manifest_review_required" ? 0 : 1;
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  cli().catch(() => {
    console.error("Integrity scan failed: unable to produce verified results");
    process.exitCode = 1;
  });
}
