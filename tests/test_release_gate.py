"""Offline safety tests for the SHA-pinned release gate."""
import importlib.util
import json
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / 'scripts' / 'release_gate.py'
spec = importlib.util.spec_from_file_location('release_gate', p)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)

HEAD = 'b' * 40
BASE = 'a' * 40


def fixture(*, generic=False, status='ahead', stale=False, checks=None, legacy=None,
            files=None, mergeable=True, draft=False, head_repo='belentani7/example'):
    pkg = {'name': 'real-product', 'description': 'Real functioning product'}
    if generic:
        pkg['description'] = 'Professional project template'
    import base64
    results = {
        '/repos/belentani7/example/pulls/7': {
            'state': 'open', 'draft': draft, 'merged': False, 'mergeable': mergeable,
            'mergeable_state': 'clean', 'head': {'sha': 'c'*40 if stale else HEAD,
                                                'repo': {'full_name': head_repo}},
            'base': {'ref': 'main', 'sha': BASE}},
        f'/repos/belentani7/example/compare/main...{HEAD}': {
            'status': status, 'ahead_by': 2, 'behind_by': 0 if status == 'ahead' else 5,
            'base_commit': {'sha': BASE}},
        '/repos/belentani7/example/pulls/7/files?per_page=100&page=1': files or [{'filename':'src/app.py','status':'modified'}],
        f'/repos/belentani7/example/contents/package.json?ref={HEAD}': {
            'content':base64.b64encode(json.dumps(pkg).encode()).decode()},
        f'/repos/belentani7/example/commits/{HEAD}/check-runs?per_page=100': {
            'total_count': 2,
            'check_runs': checks if checks is not None else [
                {'name':'build','status':'completed','conclusion':'success'},
                {'name':'tests','status':'completed','conclusion':'success'}]},
        f'/repos/belentani7/example/commits/{HEAD}/status': {
            'statuses': [{'context': 'Vercel', 'state':'success'}] if legacy is None else legacy},
    }
    return FakeClient(results)


class FakeClient:
    def __init__(self, data):
        self.data, self.writes = data, []
    def call(self, path, method='GET', payload=None):
        if path.endswith("/git/ref/heads/main"):
            return {"object": {"sha": self.data.get("_active_base", BASE)}}
        if method != 'GET':
            self.writes.append((path, method, payload))
            return {'merged':True, 'sha':'d'*40}
        if path not in self.data:
            raise AssertionError('Unexpected network path: ' + path)
        return self.data[path]


class ReleaseGateTests(unittest.TestCase):
    def check(self, client=None):
        return module.verify(client or fixture(), 'belentani7/example', 7, HEAD, ['build','tests'])
    def assertStops(self, client):
        with self.assertRaises(module.GateError):
            self.check(client)
        self.assertEqual([], client.writes)
    def test_green_shapinned_candidate_is_read_only(self):
        candidate=self.check()
        self.assertEqual(HEAD,candidate.head_sha)
        self.assertEqual(2,candidate.ahead_by)
    def test_explicit_merge_pins_commit_sha(self):
        client=fixture()
        c=self.check(client)
        result=module.merge(client,c)
        self.assertTrue(result['merged'])
        self.assertFalse(result['production_verified'])
        self.assertEqual(HEAD,client.writes[0][2]['sha'])
    def test_refuses_stale_base_at_merge_time(self):
        client=fixture()
        c=self.check(client)
        client.data["_active_base"] = "e" * 40
        with self.assertRaises(module.GateError):
            module.merge(client,c)
        self.assertEqual([], client.writes)
    def test_non404_content_errors_must_fail_closed(self):
        class BrokenClient(FakeClient):
            def call(self,path, method="GET",payload=None):
                if "/contents/package.json" in path:
                    raise module.ApiError(403,"Forbidden")
                return super().call(path,method,payload)
        self.assertStops(BrokenClient(fixture().data))
    def test_never_merges_divergent_branch(self):
        self.assertStops(fixture(status='diverged'))
    def test_never_merges_stale_head(self):
        self.assertStops(fixture(stale=True))
    def test_never_merges_other_product(self):
        self.assertStops(fixture(head_repo='belentani7/unrelated'))
    def test_never_merges_generic_manifest(self):
        self.assertStops(fixture(generic=True))
    def test_never_merges_draft(self):
        self.assertStops(fixture(draft=True))
    def test_never_merges_conflicts(self):
        self.assertStops(fixture(mergeable=False))
    def test_no_deletion_without_review(self):
        self.assertStops(fixture(files=[{'filename':'src/critical.py','status':'removed'}]))
    def test_one_failed_check_blocks(self):
        self.assertStops(fixture(checks=[{'name':'build','status':'completed','conclusion':'success'},
                                         {'name':'tests','status':'completed','conclusion':'failure'}]))
    def test_one_missing_check_blocks(self):
        self.assertStops(fixture(checks=[{'name':'build','status':'completed','conclusion':'success'}]))
    def test_vercel_failure_blocks(self):
        self.assertStops(fixture(legacy=[{'context':'Vercel','state':'failure'}]))
    def test_no_external_token_leak(self):
        with self.assertRaises(module.GateError):
            module.GitHub('')
    def test_valid_repo_name_only(self):
        with self.assertRaises(module.GateError):
            module._path('../outside')


if __name__ == '__main__':
    unittest.main()
