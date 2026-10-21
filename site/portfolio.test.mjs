import assert from "node:assert/strict";
import test from "node:test";
import { parsePortfolio, summarize, selectRows, MAX_FILE_BYTES } from "./portfolio.mjs";

const source = {
  total: 3,
  repositories: [
    { id: "1", name: "School", full_name: "belentani7/school", private: true, archived: false, category_hint: "education", default_branch: "main" },
    { id: "2", full_name: "belentani7/agent-lab", archived: false, private: true, category_hint: "ai_tools" },
    { id: "3", full_name: "belentani7/history", archived: true, private: false },
  ],
};
test("reads historical inventory without falsely granting release readiness", () => {
  const result = parsePortfolio(source);
  assert.equal(result.rows.length, 3);
  assert.equal(result.mode, "snapshot");
  assert.equal(result.rows[0].ready, false);
  assert.equal(result.rows[0].checked, false);
  assert.equal(result.rows[0].status, "unverified_snapshot");
  assert.equal(summarize(result.rows).fullyReleased, 0);
  assert.deepEqual(
    Object.entries(summarize(result.rows)).filter(([key]) => ["total","active","archived","private","public"].includes(key)),
    [["total",3],["active",2],["archived",1],["private",2],["public",1]]
  );
});
test("enforces scope rather than trusting unsupported completion claims", () => {
  const claimed = {
    ...source,
    inventory_scope: "authenticated_live_github", live_authenticated: false,
    repositories: [{ ...source.repositories[0], release_authorized: true, purpose_verified: true,
      content_verified: true, deployed_verified: true }],
    total: 1,
  };
  const data = parsePortfolio(claimed);
  assert.equal(data.mode, "snapshot");
  assert.equal(data.rows[0].ready, false);
  assert.equal(data.rows[0].checked, false);
  assert.equal(data.rows[0].purpose_verified, false);
});
test("live inventory still requires separate product validation", () => {
  const live = parsePortfolio({
    owner: "belentani7", inventory_scope: "authenticated_live_github",live_authenticated: true,
    repositories: [{...source.repositories[0],status:"manual_product_validation_required",missing:["LICENSE"],release_authorized:true}],
    total_visible: 1,
  });
  assert.equal(live.mode, "live");
  assert.equal(live.rows[0].checked, true);
  assert.equal(live.rows[0].ready, false);
  assert.deepEqual(live.rows[0].missing, ["LICENSE"]);
});
test("search, classification, sorting and active filters work on real data", () => {
  const rows = parsePortfolio(source).rows;
  assert.deepEqual(selectRows(rows, { query: "AGENT" }).map(x => x.name), ["agent-lab"]);
  assert.deepEqual(selectRows(rows, { state: "archived" }).map(x => x.name), ["history"]);
  assert.deepEqual(selectRows(rows, { category: "education" }).map(x => x.name), ["school"]);
  assert.deepEqual(selectRows(rows, { order: "name" }).map(x => x.name), ["agent-lab","history","school"]);
});
test("malformed or duplicate data never reaches presentation", () => {
  const invalid = [
    null, {}, { repositories: {} }, { owner: "a/b", repositories: [] },
    { repositories: [null] }, { repositories: [{ full_name: "../../etc/passwd" }] },
    { repositories: [source.repositories[0], source.repositories[0]] },
    { repositories: source.repositories, total: 4 },
    { repositories: Array.from({length:2001}, () => source.repositories[0]) },
  ];
  for (const value of invalid) assert.throws(() => parsePortfolio(value));
  assert.ok(MAX_FILE_BYTES <= 8 * 1024 * 1024);
});
