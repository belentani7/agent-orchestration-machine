from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from machine.factory_engine import FactoryError, FactoryStore, GitHubReader, gate, main

def inventory(count=6, archived=(5,)):
    return {"owner":"belentani7","repositories":[
        {"id":i+10,"full_name":f"belentani7/project-{i}",
         "private":True,"archived":i in archived} for i in range(count)]}

class FactoryEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db=Path(self.temp.name)/"private"/"factory.db"
        self.store=FactoryStore(self.db)
        self.addCleanup(self.store.close)

    def test_persistent_inventory_keeps_archives_out_of_work(self):
        self.assertEqual(self.store.import_inventory(inventory()),{"imported":6,"archived":1,"active":5})
        self.assertEqual(self.store.metrics()["by_status"],{"archived":1,"queued":5})
        with FactoryStore(self.db) as reopened:
            self.assertEqual(reopened.metrics()["total"],6)
        jobs=self.store.claim(limit=3)
        self.assertEqual(len(jobs),3)
        self.assertTrue(all(j["status"]=="leased" and j["attempts"]==1 for j in jobs))
        self.assertTrue(all(not j["archived"] for j in jobs))
        self.store.import_inventory(inventory())
        self.assertEqual(self.store.metrics()["by_status"]["leased"],3)

    def test_bad_inventory_rejected_atomically(self):
        original=inventory()
        bad=[
            {"owner":"attacker","repositories":original["repositories"]},
            {"owner":"belentani7","repositories":original["repositories"]*2},
            {"owner":"belentani7","repositories":[{**original["repositories"][0],"full_name":"other/repo"}]},
            {"owner":"belentani7","repositories":[{**original["repositories"][0],"archived":"false"}]},
            {"owner":"belentani7","repositories":[{**original["repositories"][0],"id":0}]},
        ]
        for item in bad:
            with self.subTest(item=item),self.assertRaises(FactoryError):
                self.store.import_inventory(item)
            self.assertEqual(self.store.metrics()["total"],0)

    def test_concurrent_connections_never_claim_same_repo(self):
        self.store.import_inventory(inventory())
        with FactoryStore(self.db) as other:
            a=self.store.claim(limit=3)
            b=other.claim(limit=3)
            self.assertEqual((len(a),len(b)),(3,2))
            self.assertTrue({x["repo_id"] for x in a}.isdisjoint({x["repo_id"] for x in b}))
            self.assertFalse(self.store.claim(limit=3))

    def test_retries_have_bounded_budget(self):
        self.store.import_inventory(inventory(count=1,archived=()))
        first=self.store.claim(limit=1,max_attempts=2)[0]
        self.store.finish(first["repo_id"],lease_token=first["lease_token"],
                          error="temporary_failure",retry_seconds=0,max_attempts=2)
        second=self.store.claim(limit=1,max_attempts=2)[0]
        self.assertNotEqual(first["lease_token"],second["lease_token"])
        self.store.finish(second["repo_id"],lease_token=second["lease_token"],
                          error="repeated_failure",retry_seconds=0,max_attempts=2)
        self.assertEqual(self.store.metrics()["by_status"],{"blocked":1})
        self.assertEqual(self.store.claim(),[])

    def test_stale_worker_cannot_overwrite_results(self):
        self.store.import_inventory(inventory(count=1,archived=()))
        job=self.store.claim(limit=1)[0]
        with self.assertRaises(FactoryError):
            self.store.finish(job["repo_id"],lease_token="stale",evidence={})
        self.store.finish(job["repo_id"],lease_token=job["lease_token"],evidence={"mode":"local"})
        with self.assertRaises(FactoryError):
            self.store.finish(job["repo_id"],lease_token=job["lease_token"],evidence={"mode":"late"})
        self.assertEqual(self.store.metrics()["by_status"],{"checked":1})

    def test_root_scan_never_implies_release(self):
        self.store.import_inventory(inventory(count=1,archived=()))
        job=self.store.claim(limit=1)[0]
        def fake_api(path):
            if path.endswith("/contents"):
                return [{"name":x} for x in ("README.md","src","tests","LICENSE")]
            return {"id":job["repo_id"],"full_name":job["full_name"],"archived":False}
        reader=GitHubReader(token="placeholder-token")
        with patch.object(reader,"get",side_effect=fake_api):
            evidence=reader.inspect(job)
        self.assertFalse(evidence["publishable"])
        self.assertEqual(evidence["state"],"requires_product_validation")
        self.store.finish(job["repo_id"],lease_token=job["lease_token"],evidence=evidence)
        export=self.store.export(include_names=True)
        self.assertEqual(export["by_status"],{"checked":1})
        self.assertNotIn("lease_token",export["repositories"][0])
        self.assertFalse(export["repositories"][0]["evidence"]["publishable"])

    def test_no_live_token_is_not_an_authentic_audit(self):
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaises(FactoryError):
                GitHubReader().get("/repos/belentani7/project")

    def test_release_gate_cannot_publish_even_with_claims(self):
        missing=gate({})
        self.assertFalse(missing["review_candidate"])
        required=("purpose_verified","homepage_verified","features_verified","content_verified",
             "security_verified","accessibility_verified","tests_verified","licenses_verified",
             "deployment_checked_from_exact_sha","rollback_tested")
        claims={key:True for key in required}
        claims.update({"commit_sha":"a"*40,"production_url":"https://example.com"})
        result=gate(claims)
        self.assertTrue(result["review_candidate"])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["production_verified_by_engine"])
        claims["production_url"]="javascript:alert(1)"
        self.assertFalse(gate(claims)["review_candidate"])

    def test_cli_import_and_export_without_private_leak(self):
        file=Path(self.temp.name)/"inventory.json"
        file.write_text(json.dumps(inventory(count=2,archived=())),encoding="utf8")
        self.assertEqual(main(["--db",str(self.db),"seed",str(file)]),0)
        self.assertEqual(main(["--db",str(self.db),"status"]),0)
        out=Path(self.temp.name)/"report.json"
        self.assertEqual(main(["--db",str(self.db),"export","--output",str(out)]),0)
        self.assertNotIn("project-",out.read_text())
        with patch.dict("os.environ",{},clear=True):
            self.assertEqual(main(["--db",str(self.db),"scan"]),2)
        self.assertEqual(self.store.metrics()["by_status"],{"queued":2})


    def test_scan_continues_after_unexpected_reader_error_without_leaking_details(self):
        self.store.import_inventory(inventory(count=3, archived=()))
        def inspect(record):
            if record["repo_id"] == 10:
                raise RuntimeError("secret-token-should-not-appear")
            return {"mode": "authenticated_read_only",
                    "state": "requires_product_validation", "publishable": False}
        with patch.dict("os.environ", {"PORTFOLIO_AUDIT_TOKEN": "synthetic-test-only"}):
            with patch.object(GitHubReader, "inspect", side_effect=inspect):
                self.assertEqual(main(["--db", str(self.db), "scan", "--limit", "3"]), 0)
        states = self.store.metrics()["by_status"]
        self.assertEqual(states, {"checked": 2, "retry": 1})
        row = self.store.db.execute(
            "SELECT last_error FROM repos WHERE repo_id=10").fetchone()
        self.assertEqual(row["last_error"], "inspection_unexpected_error")
        self.assertNotIn("secret-token", str(self.store.export(include_names=True)))

    def test_scan_preserves_sanitized_reader_errors(self):
        self.store.import_inventory(inventory(count=1, archived=()))
        with patch.dict("os.environ", {"PORTFOLIO_AUDIT_TOKEN": "synthetic-test-only"}):
            with patch.object(GitHubReader, "inspect",
                              side_effect=FactoryError("github_network_unavailable")):
                self.assertEqual(main(["--db", str(self.db), "scan", "--limit", "1"]), 0)
        row = self.store.db.execute(
            "SELECT status,last_error FROM repos WHERE repo_id=10").fetchone()
        self.assertEqual(row["status"], "retry")
        self.assertEqual(row["last_error"], "github_network_unavailable")

    def test_refresh_cycle_cannot_starve_untouched_projects(self):
        self.store.import_inventory(inventory(count=4,archived=()))
        first=self.store.claim(limit=2)
        for job in first:
            self.store.finish(job["repo_id"],lease_token=job["lease_token"],
                              evidence={"mode":"authenticated_read_only"})
        self.store.db.execute("UPDATE repos SET checked_at=checked_at-? WHERE status='checked'",
                              (74*3600,))
        pending=self.store.claim(limit=2,refresh_after_hours=72)
        self.assertEqual({x["repo_id"] for x in pending},{12,13})
        for job in pending:
            self.store.finish(job["repo_id"],lease_token=job["lease_token"],
                              evidence={"mode":"authenticated_read_only"})
        refreshed=self.store.claim(limit=2,refresh_after_hours=72)
        self.assertEqual({x["repo_id"] for x in refreshed},{10,11})
        self.assertTrue(all(x["attempts"]==1 for x in refreshed),
                        "a new review cycle resets the per-cycle retry budget")

    def test_import_archive_revokes_live_worker_lease_and_unarchive_requeues(self):
        self.store.import_inventory(inventory(count=1,archived=()))
        old=self.store.claim(limit=1)[0]
        self.store.import_inventory(inventory(count=1,archived=(0,)))
        self.assertEqual(self.store.metrics()["by_status"],{"archived":1})
        with self.assertRaises(FactoryError):
            self.store.finish(old["repo_id"],lease_token=old["lease_token"],evidence={})
        self.assertEqual(self.store.claim(limit=1),[])
        self.store.import_inventory(inventory(count=1,archived=()))
        fresh=self.store.claim(limit=1)[0]
        self.assertEqual(fresh["attempts"],1)
        self.assertNotEqual(old["lease_token"],fresh["lease_token"])

    def test_api_archiving_updates_persistent_repo_state(self):
        self.store.import_inventory(inventory(count=1,archived=()))
        record=self.store.claim(limit=1)[0]
        reader=GitHubReader(token="not-a-real-token")
        with patch.object(reader,"get",return_value={
            "id":record["repo_id"],"full_name":record["full_name"],"archived":True
        }):
            result=reader.inspect(record)
        self.store.finish(record["repo_id"],lease_token=record["lease_token"],evidence=result)
        self.assertEqual(self.store.metrics()["by_status"],{"archived":1})
        self.assertEqual(self.store.claim(limit=1),[])
        self.assertFalse(result["publishable"])

    def test_export_rejects_symlink_before_resolving_target(self):
        destination=Path(self.temp.name)/"sensitive.txt"
        destination.write_text("keep me unchanged",encoding="utf8")
        link=Path(self.temp.name)/"export.json"
        try:
            link.symlink_to(destination)
        except (OSError,NotImplementedError):
            self.skipTest("Symlinks unavailable on this platform")
        self.assertEqual(main(["--db",str(self.db),"export","--output",str(link)]),2)
        self.assertEqual(destination.read_text(encoding="utf8"),"keep me unchanged")

    def test_refresh_interval_is_bounded(self):
        self.store.import_inventory(inventory(count=1,archived=()))
        with self.assertRaises(FactoryError):
            self.store.claim(refresh_after_hours=0)
        with self.assertRaises(FactoryError):
            self.store.claim(refresh_after_hours=8761)

if __name__=="__main__":
    unittest.main()
