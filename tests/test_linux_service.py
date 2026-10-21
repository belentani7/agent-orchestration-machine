"""Static tests for Linux systemd deployment safety."""
import configparser
from pathlib import Path
import unittest

DIR = Path(__file__).resolve().parents[1] / "infra" / "systemd"


def unit(name):
    path = DIR / name
    p = configparser.ConfigParser(interpolation=None, strict=True)
    p.optionxform = str
    with path.open(encoding="utf-8") as stream:
        p.read_file(stream)
    return p


class LinuxTimerTests(unittest.TestCase):
    def test_service_has_explicit_resource_sandbox(self):
        u = unit("belentani-factory.service")
        cfg = u["Service"]
        for key in ("User", "Group", "WorkingDirectory", "ExecStartPre", "ExecStart"):
            self.assertIn(key, cfg)
        self.assertEqual("yes", cfg["NoNewPrivileges"])
        self.assertEqual("strict", cfg["ProtectSystem"])
        self.assertEqual("yes", cfg["ProtectHome"])
        self.assertEqual("0077", cfg["UMask"])
        self.assertEqual("512M", cfg["MemoryMax"])
        self.assertEqual("50%", cfg["CPUQuota"])
        self.assertIn("/var/lib/belentani-factory", cfg["ReadWritePaths"])
        self.assertIn("portfolio_audit.py", cfg["ExecStart"])
        self.assertIn("unittest", cfg["ExecStartPre"])

    def test_timer_is_persistent_bounded_and_repeatable(self):
        t = unit("belentani-factory.timer")
        self.assertEqual("true", t["Timer"]["Persistent"])
        self.assertEqual("5min", t["Timer"]["AccuracySec"])
        self.assertIn("00,04,08,12,16,20:23:00", t["Timer"]["OnCalendar"])
        self.assertEqual("belentani-factory.service", t["Timer"]["Unit"])

    def test_template_does_not_commit_live_credentials(self):
        text = (DIR / "portfolio.env.example").read_text(encoding="utf-8")
        self.assertIn("PORTFOLIO_AUDIT_TOKEN=", text)
        for bad in ("ghp_", "github_pat_", "ghu_", "ghs_"):
            self.assertNotIn(bad, text)
        self.assertNotIn("curl | sh", (DIR / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
