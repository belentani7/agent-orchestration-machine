"""Static security and accessibility smoke checks for the PRIVATE local console."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

SITE = Path(__file__).resolve().parents[1] / "site"


class Tags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.attrs = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.attrs.append((tag, data))
        if "id" in data:
            self.ids.add(data["id"])
        for key in ("src", "href"):
            if key in data and data[key]:
                self.links.append(data[key])


class ConsoleSmokeTests(unittest.TestCase):
    def setUp(self):
        self.html = (SITE / "index.html").read_text(encoding="utf-8")
        self.app = (SITE / "app.mjs").read_text(encoding="utf-8")
        self.parser = Tags()
        self.parser.feed(self.html)

    def test_entrypoint_and_assets_resolve_locally(self):
        for expected in ("index.html", "style.css", "app.mjs", "portfolio.mjs"):
            self.assertTrue((SITE / expected).is_file(), expected)
        for value in self.parser.links:
            if value.startswith("#") or value.startswith("data:"):
                continue
            self.assertFalse(value.startswith(("http:", "https:", "//", "/")),
                             f"External or absolute asset: {value}")
            path = (SITE / value.split("#", 1)[0].split("?", 1)[0]).resolve()
            self.assertTrue(path.is_relative_to(SITE.resolve()), "Resource escaped site directory")
            self.assertTrue(path.is_file(), f"Missing resource {path}")

    def test_private_noindex_and_locked_network(self):
        meta = [d for t, d in self.parser.attrs if t == "meta"]
        robots = next(d for d in meta if d.get("name") == "robots")
        self.assertIn("noindex", robots["content"])
        csp = next(d for d in meta if d.get("http-equiv") == "Content-Security-Policy")["content"]
        self.assertIn("connect-src 'none'", csp)
        self.assertIn("default-src 'none'", csp)
        self.assertNotIn("unsafe-inline", csp)
        self.assertNotIn("fetch(", self.app)
        self.assertNotIn("localStorage", self.app)
        self.assertNotIn("innerHTML", self.app)
        self.assertNotIn("sendBeacon", self.app)

    def test_accessible_navigation_controls(self):
        self.assertIn("main", [tag for tag, _ in self.parser.attrs])
        self.assertIn("file", self.parser.ids)
        self.assertIn("search", self.parser.ids)
        self.assertIn("list", self.parser.ids)
        self.assertIn("inspector", self.parser.ids)
        self.assertIn("hero-title", self.parser.ids)
        self.assertTrue(any(tag == "a" and values.get("href") == "#main"
                            for tag, values in self.parser.attrs))
        self.assertIn("prefers-reduced-motion", (SITE / "style.css").read_text())

    def test_script_cannot_have_csp_blocked_inline_handlers(self):
        for tag, attrs in self.parser.attrs:
            for name in attrs:
                self.assertFalse(name.lower().startswith("on"), f"Inline handler on {tag}: {name}")


if __name__ == "__main__":
    unittest.main()
