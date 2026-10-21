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
             patch.object(audit, "TOKEN", "test-only"), \
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
        with patch.object(audit, "TOKEN", "test-only"), patch.object(audit, "api", return_value=[
            {"name": "README.md"}, {"name": "LICENSE"}, {"name": ".gitignore"},
            {"name": "package.json"}, {"name": "src"}]):
            result = audit.inspect(sample, True)
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["deployed_verified"])
        self.assertFalse(result["content_verified"])
        self.assertEqual(result["status"], "manual_product_validation_required")

    def test_snapshotted_private_fleet_is_not_live_verification(self):
        with patch.object(audit, "TOKEN", None), \
             patch.object(audit, "api", side_effect=AssertionError("offline mode may not call API")):
            records = audit.repo_pages()
            self.assertEqual(490, len(records))
            self.assertEqual(490, len({r["id"] for r in records}))
            current = next(r for r in records if not r["archived"])
            result = audit.inspect(current, True)
            self.assertEqual("unverified_snapshot", result["status"])
            self.assertEqual("historical_snapshot_only", result["checks"]["content_audit"])
            self.assertFalse(result["release_authorized"])

    def test_offline_inventory_outputs_490_unverified_entries(self):
        with TemporaryDirectory() as folder, \
             patch.object(audit, "OUT", Path(folder)), \
             patch.object(audit, "TOKEN", None), \
             patch.object(audit, "SCOPE", "historical_snapshot_unverified"), \
             patch.object(audit, "api", side_effect=AssertionError("No HTTP API permitted")):
            self.assertEqual(0, audit.main())
            data = json.loads((Path(folder) / "inventory.json").read_text())
            self.assertEqual(490, data["total_visible"])
            self.assertEqual(0, data["contents_scanned"])
            self.assertFalse(data["live_authenticated"])
            self.assertTrue(all(not r["release_authorized"] for r in data["repositories"]))

if __name__ == "__main__":
    unittest.main()
