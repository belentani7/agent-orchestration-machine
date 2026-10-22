#!/usr/bin/env bash
set -euo pipefail

# Clone upstream source for inspection; does NOT execute third-party install scripts.
# CodeGraff is cloned for license/security review only and is NOT installed or run.
DEST="${1:-$HOME/.local/share/belentani-tools}"
mkdir -p "$DEST"
command -v git >/dev/null || { echo "ERROR: git is required" >&2; exit 2; }
# Keep the previous manifest intact until every source refresh succeeds.
MANIFEST_TMP="$(mktemp "$DEST/.CLONES.tsv.XXXXXX")"
trap 'rm -f "$MANIFEST_TMP"' EXIT

clone_or_update() {
  local repo="$1" dir="$2"
  if [[ -d "$DEST/$dir/.git" ]]; then
    echo "Updating $dir"
    if ! git -C "$DEST/$dir" diff --quiet || ! git -C "$DEST/$dir" diff --cached --quiet; then
      echo "ERROR: $dir has uncommitted changes. Save them before refreshing." >&2
      return 1
    fi
    git -C "$DEST/$dir" fetch --tags --prune origin
    git -C "$DEST/$dir" checkout --detach origin/HEAD
  else
    git clone --depth 1 "https://github.com/$repo.git" "$DEST/$dir"
  fi
  printf '%s\t%s\t%s\n' "$repo" "$(git -C "$DEST/$dir" rev-parse HEAD)" "$DEST/$dir" >> "$MANIFEST_TMP"
}

clone_or_update "obra/superpowers" "superpowers"
clone_or_update "pbakaus/impeccable" "impeccable"
clone_or_update "Graphify-Labs/graphify" "graphify"
clone_or_update "justrach/codegraff" "codegraff-review-only"

mv -- "$MANIFEST_TMP" "$DEST/CLONES.tsv"
echo
echo "Source checkouts ready for inspection in: $DEST"
echo "Recorded upstream commits in: $DEST/CLONES.tsv"
echo "No installation scripts were executed."
echo "IMPORTANT: codegraff-review-only is not installed or run; review its modified AGPL/license carve-outs first."
echo "Next: inspect each LICENSE, pin commits in your tool manifest, then install tools per editor using upstream docs."
