#!/usr/bin/env python3
"""Rebuild sitemap.xml from the static pages plus every built blog page."""
import datetime, pathlib, re, xml.sax.saxutils as x

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://linkker.space"
TODAY = datetime.date.today().isoformat()
STATIC = [("/", "weekly", "1.0"), ("/blog", "daily", "0.8"), ("/support", "monthly", "0.6"),
          ("/privacy-policy", "yearly", "0.3"), ("/terms-of-service", "yearly", "0.3"),
          ("/delete-account", "yearly", "0.3")]


def post_date(html):
    m = re.search(r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})', html) or re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', html)
    return m.group(1) if m else TODAY


urls = [(p, TODAY, cf, pr) for p, cf, pr in STATIC]
for f in sorted((ROOT / "blog").rglob("index.html")):
    rel = f.parent.relative_to(ROOT / "blog").as_posix()
    if rel == "." or rel.startswith("assets"):
        continue
    urls.append((f"/blog/{rel}", post_date(f.read_text(errors="ignore")), "monthly", "0.7"))

body = "\n".join(
    f"  <url>\n    <loc>{SITE}{x.escape(u)}</loc>\n    <lastmod>{d}</lastmod>\n"
    f"    <changefreq>{c}</changefreq>\n    <priority>{p}</priority>\n  </url>" for u, d, c, p in urls)
(ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "\n</urlset>\n")
print(f"sitemap.xml: {len(urls)} urls")
