#!/usr/bin/env bash
set -euo pipefail

# Export only repositories owned by the authenticated GitHub user.
# Requires: gh auth login, jq, sha256sum, and permission to list private repos.
OWNER="${GITHUB_OWNER:-belentani7}"
OUT="${1:-github-inventory.json}"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh is not authenticated. Run: gh auth login" >&2
  exit 2
fi
command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 2; }

# --paginate is essential: the endpoint returns at most 100 repos per page.
gh api --paginate '/user/repos?per_page=100&affiliation=owner&sort=updated&direction=desc' \
  --jq ".[] | select(.owner.login == \"$OWNER\") | {id,full_name,html_url,visibility,private,archived,default_branch,size,updated_at}" \
  > "$TMP"

if [[ ! -s "$TMP" ]]; then
  echo "ERROR: GitHub returned no repositories for owner=$OWNER" >&2
  exit 3
fi

SNAPSHOT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
jq -s --arg snapshot "$SNAPSHOT" --arg owner "$OWNER" '
  {
    snapshot_at: $snapshot,
    owner: $owner,
    source: "gh api --paginate /user/repos?per_page=100&affiliation=owner",
    count_returned: length,
    unique_ids: (map(.id) | unique | length),
    repositories: .
  }
' "$TMP" > "$OUT"

sha256sum "$OUT" > "$OUT.sha256"
echo "Inventory exported: $OUT"
jq '{snapshot_at, owner, count_returned, unique_ids}' "$OUT"
echo "SHA-256 saved to $OUT.sha256"
