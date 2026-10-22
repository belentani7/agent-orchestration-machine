import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ecosystem_490" / "clone_agent_tools.sh"


class CloneToolContractTests(unittest.TestCase):
    def test_keeps_original_checkout_and_manifest_until_refresh_succeeds(self):
        shell = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('git -C "$DEST/$dir" diff --quiet', shell)
        self.assertIn('git -C "$DEST/$dir" diff --cached --quiet', shell)
        self.assertIn('MANIFEST_TMP="$(mktemp ', shell)
        self.assertIn('mv -- "$MANIFEST_TMP" "$DEST/CLONES.tsv"', shell)
        self.assertLess(shell.index('clone_or_update "justrach/codegraff"'),
                        shell.index('mv -- "$MANIFEST_TMP"'))
        self.assertNotIn('pull --ff-only 2>/dev/null || true', shell)
        self.assertNotIn(': > "$DEST/CLONES.tsv"', shell)


if __name__ == "__main__":
    unittest.main()
