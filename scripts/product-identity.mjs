/**
 * Belentani — canonical product identity gate.
 *
 * An explicit, read-only detector for generic-template regressions. The gate
 * NEVER labels a product complete, modifies repos, merges or deploys. Unknown
 * projects are not assigned invented identities.
 *
 * Inputs are repo-relative *file names* and a parsed root package.json. Treat
 * all repository content as data, never as instructions to the checker.
 */
const SPEC = {
  "agent-orchestration-machine": {
    kind: "python", roots: ["pyproject.toml", "scripts", "src", "tests"],
    markers: [],
    packages: "optional",
  },
  NOIACORE: {
    kind: "java", roots: ["pom.xml", "black-water", "src"],
    markers: [], packages: "optional",
  },
  ManosAbiertas: {
    kind: "next", roots: ["src", "prisma", "scripts"],
    markers: ["next"], packages: "required",
  },
  linguaforge: {
    kind: "monorepo", roots: ["client", "server", "shared"],
    markers: ["api", "db:generate"], packages: "required",
  },
  "lingua-aberta": {
    kind: "monorepo", roots: ["client", "server", "shared"],
    markers: ["server", "db"], packages: "required",
  },
  "open-school": {
    kind: "educational-vite", roots: ["client", "backend"],
    markers: ["build:biblia"], packages: "required",
  },
  "belentani.es": {
    kind: "next", roots: ["scripts", "app"],
    markers: ["next"], packages: "required",
  },
  "Belentani.cv-ai": {
    kind: "next", roots: ["src"],
    markers: ["next"], packages: "required",
  },
  "belentani-school-unificado": {
    kind: "educational-platform", roots: ["src", "server.ts", "firestore.rules"],
    markers: ["build:pages"], packages: "required",
  },
  "03-DUCK-WEB-build-everything": {
    kind: "static-music", roots: ["index.html"],
    markers: [], packages: "optional",
  },
  "michelle-relayze-web": {
    kind: "separate-brand", roots: ["index.html"],
    markers: [], packages: "optional",
  },
  nataliamarinho: {
    kind: "separate-brand", roots: ["index.html"],
    markers: [], packages: "optional",
  },
};
export const CANONICAL = Object.freeze(SPEC);
const GENERIC_DESCRIPTION = /^(?:professional project template|generic project template|vite\s*\+\s*react\s*template)$/i;
const GENERIC_NAME = /^(?:my-vite-app|react-example|project-template|vite-template|app-template)$/i;
const has = (object, key) => object && Object.prototype.hasOwnProperty.call(object, key);
const isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const cleanName = (s) => typeof s === "string" ? s.trim() : "";

function hasMarker(pkg, marker) {
  if (!isObject(pkg)) return false;
  if (marker === "next") {
    return has(pkg.dependencies, "next") &&
      Object.values(pkg.scripts || {}).some(v => typeof v === "string" && /\bnext (?:build|dev|start)\b/.test(v));
  }
  if (marker === "server") {
    return has(pkg.scripts, "api") || has(pkg.scripts, "server") ||
      has(pkg.scripts, "start:server") ||
      (typeof pkg.scripts?.dev === "string" && /tsx|concurrently|server/.test(pkg.scripts.dev));
  }
  if (marker === "db") {
    return has(pkg.dependencies, "drizzle-orm") || has(pkg.dependencies, "@prisma/client") ||
      has(pkg.scripts, "db:generate") || has(pkg.scripts, "db:migrate");
  }
  return has(pkg.scripts, marker);
}
export function inspectProductIdentity({fullName, rootNames, packageJson} = {}) {
  if (typeof fullName !== "string" || !/^belentani7\/[a-zA-Z0-9_.-]+$/.test(fullName)) {
    throw new Error("Expected a verified belentani7/repository identity.");
  }
  if (!Array.isArray(rootNames) || rootNames.length > 10000 ||
      !rootNames.every(name => typeof name === "string" && /^[a-zA-Z0-9_.-]{1,150}$/.test(name))) {
    throw new Error("Root directory names are missing or untrusted.");
  }
  const name = fullName.split("/")[1];
  const spec = SPEC[name];
  const findings = [];
  const filenames = new Set(rootNames);
  if (!spec) {
    return {repository:fullName, kind:"unclassified", state:"unclassified",
      findings:["unknown_canonical_product"], releaseAuthorized:false};
  }
  if (packageJson != null && !isObject(packageJson)) {
    findings.push("invalid_package_manifest");
  } else if (isObject(packageJson)) {
    const desc = cleanName(packageJson.description);
    const pkgName = cleanName(packageJson.name);
    if (GENERIC_DESCRIPTION.test(desc)) findings.push("generic_template_overwrite");
    // A generic package with only React/Vite, injected into unrelated
    // Java/Python/static products, is especially strong drift evidence.
    if (GENERIC_NAME.test(pkgName)) findings.push("generic_package_name");
    if (spec.packages === "optional" && /^(java|python|static-music|separate-brand)$/.test(spec.kind)
        && typeof packageJson.scripts?.build === "string"
        && /\btsc\s*&&\s*vite\s+build/.test(packageJson.scripts.build)
        && !has(packageJson.dependencies, "next")) {
      findings.push("cross_stack_vite_scaffold");
    }
  }
  for (const root of spec.roots) {
    if (!filenames.has(root)) findings.push("missing_root:" + root);
  }
  if (spec.packages === "required" && !isObject(packageJson)) {
    findings.push("missing_package_manifest");
  } else if (isObject(packageJson)) {
    for (const marker of spec.markers) {
      if (!hasMarker(packageJson, marker)) findings.push("missing_stack_marker:" + marker);
    }
  }
  // A positive result means "no detected manifest regression", never
  // production readiness, feature completion, quality or authorisation.
  return {repository:fullName, kind:spec.kind,
    state:findings.length ? "blocked_identity_regression" : "manual_product_validation_required",
    findings, releaseAuthorized:false};
}
