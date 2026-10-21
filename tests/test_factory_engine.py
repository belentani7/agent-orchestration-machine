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

if __name__=="__main__":
    unittest.main()
