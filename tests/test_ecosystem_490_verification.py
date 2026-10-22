import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ecosystem_490/generate_verification.py"


class VerificationGeneratorTests(unittest.TestCase):
    def test_generates_two_distinct_reports_then_preserves_existing_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "inventory.json"
            out = root / "reports"
            source.write_text(json.dumps({"repositories": [
                {"full_name": "belentani7/NOIACORE"},
                {"full_name": "belentani7/ManosAbiertas"}
            ]}), encoding="utf-8")
            cmd = [sys.executable, str(SCRIPT), str(source), "--out", str(out)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(len(json.loads((out / "manifest.json").read_text())), 2)
            generated = out / "belentani7__NOIACORE" / "VERIFICACION.md"
            self.assertIn("NOT RUN", generated.read_text())
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertTrue(generated.exists())

    def test_rejects_colliding_names_before_creating_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "inventory.json"
            out = root / "reports"
            source.write_text(json.dumps({"repositories": [
                {"full_name": "a/b__c"}, {"full_name": "a__b/c"}
            ]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--out", str(out)],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Report path collision", result.stderr)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
