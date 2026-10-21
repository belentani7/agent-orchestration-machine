"""Persistent, read-only portfolio work queue. Python 3.11+, standard library."""
from __future__ import annotations
import argparse
import contextlib
import datetime as dt
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

OWNER = "belentani7"
API_URL = "https://api.github.com"
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
CREATE TABLE IF NOT EXISTS repos (
 repo_id INTEGER PRIMARY KEY,
 full_name TEXT NOT NULL UNIQUE COLLATE NOCASE,
 private INTEGER NOT NULL CHECK(private IN (0,1)),
 archived INTEGER NOT NULL CHECK(archived IN (0,1)),
 status TEXT NOT NULL CHECK(status IN ('queued','leased','checked','retry','blocked','archived')),
 priority INTEGER NOT NULL DEFAULT 0,
 attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
 lease_until REAL,
 lease_token TEXT,
 available_at REAL NOT NULL DEFAULT 0,
 checked_at REAL,
 evidence_json TEXT,
 last_error TEXT NOT NULL DEFAULT '',
 updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_repos_queue ON repos(status,available_at,priority,updated_at);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 repo_id INTEGER NOT NULL REFERENCES repos(repo_id),
 created_at REAL NOT NULL,
 kind TEXT NOT NULL,
 payload TEXT NOT NULL
);
"""

class FactoryError(ValueError):
    """Invalid input or unsafe operation."""

def _now() -> float:
    return time.time()

def _snapshot(row: sqlite3.Row, *, include_lease: bool = False) -> dict[str, Any]:
    result = dict(row)
    result["private"] = bool(result["private"])
    result["archived"] = bool(result["archived"])
    if not include_lease:
        result.pop("lease_token", None)
    if result.get("evidence_json"):
        result["evidence"] = json.loads(result.pop("evidence_json"))
    else:
        result.pop("evidence_json", None)
        result["evidence"] = None
    return result

def validate_repository(row: Any, owner: str = OWNER) -> tuple[int, str, bool, bool]:
    if not isinstance(row, dict):
        raise FactoryError("Repository entry must be an object")
    name = row.get("full_name")
    if not isinstance(name, str) or name.count("/") != 1:
        raise FactoryError("Repository must use owner/name")
    repo_owner, repo_name = name.split("/", 1)
    if repo_owner.lower() != owner.lower() or not REPO_PATTERN.fullmatch(repo_name):
        raise FactoryError("Repository outside authorized owner or invalid name")
    rid = row.get("id")
    if isinstance(rid, bool) or not str(rid).isdigit() or int(rid) < 1:
        raise FactoryError("Repository needs its immutable positive GitHub ID")
    if not isinstance(row.get("private"), bool) or not isinstance(row.get("archived"), bool):
        raise FactoryError("Repository private/archived flags must be booleans")
    return int(rid), f"{owner}/{repo_name}", row["private"], row["archived"]

class FactoryStore:
    """SQLite WAL persistent queue; BEGIN IMMEDIATE serializes leases."""
    def __init__(self, filename: str | Path):
        self.filename = Path(filename).expanduser()
        self.filename.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.filename.is_symlink():
            raise FactoryError("Refusing symlinked database path")
        previous = os.umask(0o077) if os.name == "posix" else None
        try:
            self.db = sqlite3.connect(self.filename, timeout=10, isolation_level=None)
            self.db.row_factory = sqlite3.Row
            self.db.executescript(SCHEMA)
        finally:
            if previous is not None:
                os.umask(previous)
        if os.name == "posix":
            os.chmod(self.filename, 0o600)

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_: Any):
        self.close()

    @contextlib.contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    def import_inventory(self, payload: Any) -> dict[str, int]:
        if not isinstance(payload, dict) or not isinstance(payload.get("repositories"), list):
            raise FactoryError("Invalid portfolio inventory format")
        if payload.get("owner", OWNER) != OWNER:
            raise FactoryError("Inventory owner differs from configured portfolio")
        entries = payload["repositories"]
        if not 0 < len(entries) <= 2000:
            raise FactoryError("Inventory must contain 1–2000 repositories")
        parsed = [validate_repository(r) for r in entries]
        if len({x[0] for x in parsed}) != len(parsed):
            raise FactoryError("Duplicate GitHub repository IDs")
        if len({x[1].lower() for x in parsed}) != len(parsed):
            raise FactoryError("Duplicate repository full names")
        stamp = _now()
        with self.transaction():
            for rid, name, private, archived in parsed:
                old = self.db.execute("SELECT status,archived FROM repos WHERE repo_id=?", (rid,)).fetchone()
                previous_archived = old is not None and bool(old["archived"])
                # Archiving invalidates any worker lease immediately. A newly
                # unarchived project gets a new review cycle, not stale approval.
                state = ("archived" if archived else
                         "queued" if old is None or previous_archived else old["status"])
                reset = old is not None and (archived or previous_archived)
                self.db.execute("""
                  INSERT INTO repos(repo_id,full_name,private,archived,status,updated_at)
                  VALUES(?,?,?,?,?,?) ON CONFLICT(repo_id) DO UPDATE SET
                    full_name=excluded.full_name,private=excluded.private,
                    archived=excluded.archived,status=excluded.status,
                    updated_at=excluded.updated_at
                """, (rid, name, int(private), int(archived), state, stamp))
                if reset:
                    self.db.execute("""UPDATE repos SET attempts=0,lease_until=NULL,
                        lease_token=NULL,available_at=0,last_error='',evidence_json=NULL,
                        checked_at=NULL WHERE repo_id=?""", (rid,))
            self.db.execute("INSERT INTO events(repo_id,created_at,kind,payload) VALUES(?,?,?,?)",
                            (parsed[0][0], stamp, "inventory_import", json.dumps({"count":len(parsed)})))
        return {"imported":len(parsed),"archived":sum(r[3] for r in parsed),
                "active":sum(not r[3] for r in parsed)}

    def claim(self, *, limit: int = 3, lease_seconds: int = 300, max_attempts: int = 3,
              refresh_after_hours: int = 72) -> list[dict[str, Any]]:
        if (not 1 <= limit <= 10 or not 30 <= lease_seconds <= 3600
                or not 1 <= max_attempts <= 10 or not 1 <= refresh_after_hours <= 8760):
            raise FactoryError("Bounded claim parameters required")
        now = _now()
        with self.transaction():
            self.db.execute("""UPDATE repos SET status='retry',available_at=?,lease_until=NULL,lease_token=NULL
                             WHERE status='leased' AND lease_until < ? AND attempts < ?""", (now,now,max_attempts))
            self.db.execute("""UPDATE repos SET status='blocked',last_error='lease_attempts_exhausted',
                             lease_until=NULL,lease_token=NULL
                             WHERE status='leased' AND lease_until < ? AND attempts >= ?""", (now,max_attempts))
            rows = self.db.execute("""SELECT * FROM repos
                    WHERE archived=0 AND status IN ('queued','retry') AND available_at <= ?
                      AND attempts < ?
                    ORDER BY priority DESC,COALESCE(checked_at,0),updated_at,repo_id LIMIT ?""",
                    (now,max_attempts,limit)).fetchall()
            # Only rescan previously checked records after fresh/failed work
            # is exhausted. This prevents a small group from starving the fleet.
            if len(rows) < limit:
                rows.extend(self.db.execute("""SELECT * FROM repos
                    WHERE archived=0 AND status='checked' AND checked_at <= ?
                    ORDER BY checked_at,repo_id LIMIT ?""",
                    (now-refresh_after_hours*3600,limit-len(rows))).fetchall())
            for row in rows:
                self.db.execute("""UPDATE repos SET status='leased',
                             attempts=CASE WHEN status='checked' THEN 1 ELSE attempts+1 END,
                             lease_until=?,lease_token=?,updated_at=? WHERE repo_id=?""",
                             (now+lease_seconds,uuid.uuid4().hex,now,row["repo_id"]))
            return [_snapshot(self.db.execute("SELECT * FROM repos WHERE repo_id=?",
                        (row["repo_id"],)).fetchone(),include_lease=True) for row in rows]

    def finish(self, repo_id: int, *, lease_token: str, evidence: dict[str, Any] | None = None,
               error: str | None = None, retry_seconds: int = 120, max_attempts: int = 3) -> None:
        if (evidence is None) == (error is None):
            raise FactoryError("Supply exactly one of evidence or error")
        if not 0 <= retry_seconds <= 86400:
            raise FactoryError("Invalid retry delay")
        stamp = _now()
        with self.transaction():
            row = self.db.execute("SELECT * FROM repos WHERE repo_id=?", (repo_id,)).fetchone()
            if row is None or row["status"] != "leased" or row["lease_until"] < stamp or row["lease_token"] != lease_token:
                raise FactoryError("Only the current active lease owner can finish a job")
            if evidence is not None:
                if not isinstance(evidence,dict) or len(json.dumps(evidence)) > 30000:
                    raise FactoryError("Evidence must be a small JSON object")
                confirmed_archived = evidence.get("state") == "archived"
                state = "archived" if row["archived"] or confirmed_archived else "checked"
                encoded = json.dumps(evidence,ensure_ascii=False,sort_keys=True)
                self.db.execute("""UPDATE repos SET status=?,evidence_json=?,last_error='',
                                 archived=?,checked_at=?,lease_until=NULL,
                                 lease_token=NULL,updated_at=? WHERE repo_id=?""",
                                (state,encoded,int(row["archived"] or confirmed_archived),
                                 stamp,stamp,repo_id))
                audit = {"result":state,"evidence_mode":evidence.get("mode","unknown")}
            else:
                state = ("archived" if row["archived"] else
                         "retry" if row["attempts"] < max_attempts else "blocked")
                message = (error or "unknown_error")[:240]
                self.db.execute("""UPDATE repos SET status=?,last_error=?,lease_until=NULL,
                                 available_at=?,lease_token=NULL,updated_at=? WHERE repo_id=?""",
                                (state,message,stamp+retry_seconds,stamp,repo_id))
                audit={"result":state,"error_code":message}
            self.db.execute("INSERT INTO events(repo_id,created_at,kind,payload) VALUES(?,?,?,?)",
                            (repo_id,stamp,"job_finished",json.dumps(audit)))

    def metrics(self) -> dict[str, Any]:
        counts={row[0]:row[1] for row in self.db.execute("SELECT status,COUNT(*) FROM repos GROUP BY status")}
        return {"total":sum(counts.values()),"by_status":counts,"published_verified":0,
                "note":"Inventory checks never certify releases"}

    def export(self, *, include_names: bool = False) -> dict[str, Any]:
        result={"generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),**self.metrics()}
        if include_names:
            result["repositories"]=[_snapshot(row) for row in self.db.execute("SELECT * FROM repos ORDER BY full_name")]
            result["privacy_notice"]="Sensitive private inventory: never publish on a public host"
        return result

class GitHubReader:
    """Two read-only GitHub API requests per repo, no code execution."""
    def __init__(self, token: str | None = None, *, timeout: int = 15):
        self.token=token or os.environ.get("PORTFOLIO_AUDIT_TOKEN")
        self.timeout=timeout

    def get(self, path: str) -> Any:
        if not self.token:
            raise FactoryError("missing_read_only_github_token")
        if not path.startswith("/repos/belentani7/"):
            raise FactoryError("Unexpected API path")
        req=urllib.request.Request(API_URL+path,headers={
            "Authorization":"Bearer "+self.token,
            "Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28",
            "User-Agent":"Belentani-Factory-ReadOnly/1"})
        try:
            with urllib.request.urlopen(req,timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code in (401,403,429):
                raise FactoryError("github_unauthorized_or_rate_limited") from error
            if error.code==404:
                raise FactoryError("github_repo_not_accessible") from error
            raise FactoryError("github_http_error") from error
        except (TimeoutError,urllib.error.URLError) as error:
            raise FactoryError("github_network_unavailable") from error

    def inspect(self, record: dict[str, Any]) -> dict[str, Any]:
        _,name,_,_=validate_repository({"id":record["repo_id"],
            "full_name":record["full_name"],"private":record["private"],"archived":record["archived"]})
        slug=urllib.parse.quote(name.split("/",1)[1],safe="")
        path=f"/repos/{OWNER}/{slug}"
        repo=self.get(path)
        if int(repo.get("id",0))!=record["repo_id"] or repo.get("full_name","").lower()!=name.lower():
            raise FactoryError("github_identity_mismatch")
        if repo.get("archived"):
            return {"mode":"authenticated_read_only","repo_id":record["repo_id"],
                    "state":"archived","publishable":False}
        files=self.get(path+"/contents")
        if not isinstance(files,list):
            raise FactoryError("github_root_listing_unavailable")
        names=sorted(item["name"] for item in files if isinstance(item,dict) and isinstance(item.get("name"),str))
        markers={key:key in names for key in ("README.md","LICENSE","package.json","pyproject.toml",
                  "index.html","src","app","tests",".github")}
        missing=[]
        if not markers["README.md"]:missing.append("document_real_purpose")
        if not (markers["index.html"] or markers["src"] or markers["app"]):
            missing.append("inspect_home_and_application")
        if not (markers["tests"] or markers[".github"]):missing.append("add_reproducible_tests")
        return {"mode":"authenticated_read_only","repo_id":record["repo_id"],
                "state":"requires_product_validation","publishable":False,"root_markers":markers,
                "next_checks":missing or ["verify_claimed_features_content_tests_and_production_url"],
                "root_scan_count":len(names)}

def gate(evidence: Any) -> dict[str, Any]:
    """Incomplete evidence checklist only; NEVER permission to deploy."""
    keys=("purpose_verified","homepage_verified","features_verified","content_verified",
          "security_verified","accessibility_verified","tests_verified","licenses_verified",
          "deployment_checked_from_exact_sha","rollback_tested")
    if not isinstance(evidence,dict):
        raise FactoryError("Evidence must be JSON")
    missing=[k for k in keys if evidence.get(k) is not True]
    sha=evidence.get("commit_sha")
    url=evidence.get("production_url")
    if not isinstance(sha,str) or not re.fullmatch(r"[0-9a-f]{40}",sha):
        missing.append("verified_commit_sha")
    if not isinstance(url,str) or not re.fullmatch(r"https://[A-Za-z0-9.-]+(?:/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*)?",url):
        missing.append("reachable_production_url")
    return {"review_candidate":not missing,"missing_evidence":missing,
            "release_authorized":False,"production_verified_by_engine":False}

def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description="BELENTANI Factory — bounded Python portfolio processor")
    parser.add_argument("--db",default=str(Path.home()/".local/state/belentani-factory/factory.db"))
    sub=parser.add_subparsers(dest="command",required=True)
    seed=sub.add_parser("seed",help="Import inventory into private SQLite")
    seed.add_argument("inventory",type=Path)
    scan=sub.add_parser("scan",help="Perform a bounded batch of live read-only checks")
    scan.add_argument("--limit",type=int,default=3)
    sub.add_parser("status",help="Aggregate metrics; no repository names")
    exp=sub.add_parser("export",help="Export a private JSON report")
    exp.add_argument("--include-names",action="store_true")
    exp.add_argument("--output",type=Path,required=True)
    review=sub.add_parser("gate",help="List missing release evidence")
    review.add_argument("evidence",type=Path)
    args=parser.parse_args(argv)
    try:
        if args.command=="gate":
            print(json.dumps(gate(json.loads(args.evidence.read_text(encoding="utf8"))),indent=2))
            return 0
        with FactoryStore(args.db) as store:
            if args.command=="seed":
                print(json.dumps(store.import_inventory(json.loads(args.inventory.read_text(encoding="utf8")))))
            elif args.command=="status":
                print(json.dumps(store.metrics()))
            elif args.command=="export":
                requested=args.output.expanduser()
                if requested.is_symlink():
                    raise FactoryError("Refusing symlinked output")
                output=requested.resolve()
                output.parent.mkdir(parents=True,exist_ok=True)
                output.write_text(json.dumps(store.export(include_names=args.include_names),indent=2,
                                             ensure_ascii=False)+"\n",encoding="utf8")
                if os.name=="posix":
                    os.chmod(output,0o600)
                print(json.dumps({"exported":str(output),"includes_private_names":args.include_names}))
            elif args.command=="scan":
                reader=GitHubReader()
                if not reader.token:
                    raise FactoryError("Configure a read-only PORTFOLIO_AUDIT_TOKEN before live scanning")
                claimed=store.claim(limit=args.limit)
                counters={"claimed":len(claimed),"checked":0,"retry":0}
                for job in claimed:
                    try:
                        evidence=reader.inspect(job)
                        store.finish(job["repo_id"],lease_token=job["lease_token"],evidence=evidence)
                        counters["checked"]+=1
                    except FactoryError as error:
                        store.finish(job["repo_id"],lease_token=job["lease_token"],error=str(error))
                        counters["retry"]+=1
                print(json.dumps(counters))
        return 0
    except (FactoryError,OSError,ValueError,sqlite3.Error) as error:
        print("Factory error: "+str(error)[:200],file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
