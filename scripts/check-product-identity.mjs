#!/usr/bin/env node
/**
 * Usage: node scripts/check-product-identity.mjs belentani7/repository [checkout-root]
 * Read-only, offline. Exit 1 on detected product regression, 2 on unknown/error,
 * 0 on manifest consistency. Exit 0 NEVER means product complete/published.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { resolve, join } from "node:path";
import { inspectProductIdentity } from "./product-identity.mjs";

const name = process.argv[2];
const root = resolve(process.argv[3] || process.cwd());
if (!name || process.argv.length > 4) {
  console.error("Usage: node scripts/check-product-identity.mjs belentani7/repo [root]");
  process.exit(2);
}
try {
  const names = readdirSync(root);
  let pkg = null;
  if (names.includes("package.json")) {
    const file = join(root, "package.json");
    if (statSync(file).size > 512_000) {
      throw new Error("Package manifest exceeds 500 KiB limit.");
    }
    pkg = JSON.parse(readFileSync(file, "utf8"));
  }
  const result = inspectProductIdentity({ fullName: name, rootNames: names, packageJson: pkg });
  process.stdout.write(JSON.stringify(result, null, 2) + "\n");
  if (result.state === "blocked_identity_regression") process.exitCode = 1;
  if (result.state === "unclassified") process.exitCode = 2;
} catch (err) {
  console.error(JSON.stringify({state:"error",message:err instanceof Error ? err.message : "unreadable checkout"}));
  process.exitCode = 2;
}
