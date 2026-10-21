"""No-network tests for the read-only GitHub portfolio inventory."""
import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "scripts" / "portfolio_audit.py"
spec = importlib.util.spec_from_file_location("portfolio_audit", PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class PortfolioAuditTests(unittest.TestCase):
    def test_rotating_selection_wraps_without_skipping(self):
        candidates = [{"name": f"project-{i}"} for i in range(5)]
        visits = []
        def fake_inspect(repo, scan):
            visits.append((repo["name"], scan))
            return {"name": repo["name"], "status": "needs_review", "missing": [],
                    "category_hint": "unclassified", "release_authorized": False}
        with TemporaryDirectory() as folder, \
             patch.object(audit, "OUT", Path(folder)), \
             patch.object(audit, "MAX_CONTENT_CHECKS", 2), \
             patch.object(audit, "repo_pages", return_value=candidates), \
             patch.object(audit, "inspect", side_effect=fake_inspect), \
             patch.dict(os.environ, {"AUDIT_SCAN_OFFSET": "4"}):
            self.assertEqual(audit.main(), 0)
            payload = json.loads((Path(folder) / "inventory.json").read_text())
            self.assertEqual(payload["contents_scanned"], 2)
            self.assertEqual(payload["scan_offset"], 4)
            self.assertEqual([name for name, done in visits if done],
                             ["project-0", "project-4"])
            self.assertTrue((Path(folder) / "report.md").is_file())

    def test_no_repos_writes_empty_inventory(self):
        with TemporaryDirectory() as folder, \
             patch.object(audit, "OUT", Path(folder)), \
             patch.object(audit, "repo_pages", return_value=[]):
            self.assertEqual(audit.main(), 0)
            payload = json.loads((Path(folder) / "inventory.json").read_text())
            self.assertEqual(payload["total_visible"], 0)
            self.assertEqual(payload["contents_scanned"], 0)

    def test_root_listing_is_not_release_approval(self):
        sample = {"name": "example", "full_name": "belentani7/example",
                  "archived": False, "fork": False}
        with patch.object(audit, "api", return_value=[
            {"name": "README.md"}, {"name": "LICENSE"}, {"name": ".gitignore"},
            {"name": "package.json"}, {"name": "src"}]):
            result = audit.inspect(sample, True)
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["deployed_verified"])
        self.assertFalse(result["content_verified"])
        self.assertEqual(result["status"], "manual_product_validation_required")

if __name__ == "__main__":
    unittest.main()
