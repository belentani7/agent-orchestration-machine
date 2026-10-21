import test from "node:test";
import assert from "node:assert/strict";
import { CANONICAL } from "../scripts/product-identity.mjs";
import { scanCanonicalPortfolio } from "../scripts/scan-canonical-portfolio.mjs";

test("without explicit private token does not misrepresent snapshot as live", async () => {
  const result = await scanCanonicalPortfolio({
    fetcher() {throw Error("No HTTP request expected");},
  });
  assert.equal(result.scope, "unverified_no_private_token");
  assert.equal(result.checked, 0);
  assert.equal(result.repositories.length, 0);
  assert.equal(result.status, "not_scanned");
});

test("authenticated scan reads only allowlisted repos, reports template drift", async () => {
  const requested = [];
  const fetcher = async (url,opts) => {
    requested.push({url,auth:opts.headers.Authorization});
    const path = new URL(url).pathname;
    const name = decodeURIComponent(path.split("/")[3]);
    const spec = CANONICAL[name];
    assert.ok(spec, "non-canonical repository must never be fetched");
    const isPackage = path.endsWith("/package.json");
    const packageExists = name !== "NOIACORE" && name !== "agent-orchestration-machine" &&
      name !== "03-DUCK-WEB-build-everything" &&
      name !== "nataliamarinho" && name !== "michelle-relayze-web";
    const roots = spec.roots.concat(packageExists ? ["package.json"] : []);
    const pack = {
      name, scripts: {"build:biblia":"node build", "build:pages":"node build",
        api:"tsx server", "db:generate":"drizzle-kit generate",
        check:"tsc --noEmit",build:"next build"},
      dependencies:{next:"14.2.35"},
    };
    if (name === "linguaforge") pack.description = "Professional project template";
    const body = isPackage ? {encoding:"base64",size:100,content:Buffer.from(JSON.stringify(pack)).toString("base64")}
      : roots.map(x=>({name:x}));
    return {ok:true,status:200,json:async()=>body};
  };
  const report = await scanCanonicalPortfolio({token:"test-private-read-only",fetcher});
  assert.equal(report.scope,"authenticated_github_current_checkout");
  assert.equal(report.repositories.length,Object.keys(CANONICAL).length);
  assert.equal(report.status,"blocked_regressions_present");
  const affected = report.repositories.find(x=>x.repository==="belentani7/linguaforge");
  assert.ok(affected.findings.includes("generic_template_overwrite"));
  assert.ok(requested.every(x=>x.auth==="Bearer test-private-read-only"));
  assert.ok(requested.every(x=>x.url.startsWith("https://api.github.com/repos/belentani7/")));
  assert.equal(report.releaseAuthorized,false);
});

test("HTTP and token errors never expose secrets into inventory output", async () => {
  const key = "secret-testing-opaque-key";
  const report = await scanCanonicalPortfolio({token:key,fetcher:async()=>{
    throw new Error("HTTP failure with leaked token " + key);
  }});
  assert.equal(report.status,"incomplete_unverified");
  assert.ok(report.repositories.every(r=>r.state==="inspection_unverified"));
  assert.ok(!JSON.stringify(report).includes(key));
});
