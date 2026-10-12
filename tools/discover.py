#!/usr/bin/env python3
"""Make every published post easy to find for search engines and AI assistants.

    discover.py build             write blog/feed.xml, refresh llms.txt and the homepage block
    discover.py ping URL [URL..]  tell IndexNow (Bing, Copilot/ChatGPT search, Yandex...) they changed
    discover.py ping-all          announce every URL in sitemap.xml

publish.sh runs `build` before the deploy and `ping` after it.
"""
import datetime, email.utils, html, json, re, sys, urllib.error, urllib.request

from common import ROOT, SITE, entries, POSTS

KEY_FILE = ROOT / "content" / "indexnow.key"
START, END = "<!-- articles:start -->", "<!-- articles:end -->"
HOME_START, HOME_END = "<!-- latest-posts:start -->", "<!-- latest-posts:end -->"


def posts():
    out = []
    for f, fm in entries(POSTS):
        out.append({"slug": f.stem, "title": fm["title"], "desc": fm.get("description", ""),
                    "date": str(fm.get("date", ""))[:10], "hero": fm.get("hero", ""),
                    "kicker": fm.get("kicker", "Linkker picks"), "url": f"{SITE}/blog/{f.stem}"})
    return sorted(out, key=lambda p: (p["date"], p["slug"]), reverse=True)


def rfc822(d):
    try:
        dt = datetime.datetime.strptime(d, "%Y-%m-%d").replace(hour=13, tzinfo=datetime.timezone.utc)
    except ValueError:
        dt = datetime.datetime.now(datetime.timezone.utc)
    return email.utils.format_datetime(dt)


def write_feed(ps):
    e = html.escape
    items = "\n".join(f"""    <item>
      <title>{e(p['title'])}</title>
      <link>{p['url']}</link>
      <guid isPermaLink="true">{p['url']}</guid>
      <pubDate>{rfc822(p['date'])}</pubDate>
      <description>{e(p['desc'])}</description>
      <enclosure url="{SITE}/blog{e(p['hero'])}" type="image/jpeg" length="0"/>
    </item>""" for p in ps[:40])
    (ROOT / "blog").mkdir(exist_ok=True)
    (ROOT / "blog" / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The Linkker blog</title>
    <link>{SITE}/blog</link>
    <atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Hand-picked free websites and AI tools, and smarter ways to save the links that matter.</description>
    <language>en</language>
    <lastBuildDate>{email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))}</lastBuildDate>
{items}
  </channel>
</rss>
""")


def write_llms(ps):
    p = ROOT / "llms.txt"
    text = p.read_text() if p.exists() else (
        "# Linkker\n\n> Linkker saves links from anywhere (Chrome, iPhone, Android), sorts them into smart "
        "AI categories and finds them in seconds. Private links can sit behind a PIN or biometrics, and links "
        "and files move between phone and computer over your own Wi-Fi.\n\n"
        "## Pages\n- [Home](https://linkker.space/): what Linkker does and where to get it\n"
        "- [Support](https://linkker.space/support): help and contact\n"
        "- [Blog](https://linkker.space/blog): hand-picked free websites and AI tools\n")
    block = (f"{START}\n## Articles\nHand-picked lists of free websites and tools. Each page opens with "
             "quick picks, then one honest card per site.\n\n"
             + "\n".join(f"- [{a['title']}]({a['url']}): {a['desc']}" for a in ps) + f"\n{END}")
    if START in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    p.write_text(text)


def write_homepage(ps, n=3):
    """Newest posts on the homepage, the page Google trusts most, just above the FAQ."""
    p = ROOT / "index.html"
    text = p.read_text()
    if not ps:                                 # nothing published: no block on the homepage
        text = re.sub(r"\n\s*" + re.escape(HOME_START) + r".*?" + re.escape(HOME_END), "", text, flags=re.S)
        p.write_text(text); return
    e = html.escape
    cards = "\n".join(f"""          <li><a class="post-card" href="/blog/{a['slug']}">
            <img src="/blog{e(a['hero'])}" alt="" width="1200" height="630" loading="lazy" decoding="async">
            <span class="pc-body"><small>{e(a['kicker'])}</small><b>{e(a['title'])}</b></span>
          </a></li>""" for a in ps[:n])
    block = f"""{HOME_START}
    <section class="section wrap" id="blog" aria-labelledby="blog-heading">
      <link rel="stylesheet" href="/assets/blog.css">
      <p class="eyebrow">From the blog</p>
      <h2 id="blog-heading">Useful corners of the internet, worth saving.</h2>
      <ul class="post-grid" style="margin:28px 0 18px">
{cards}
      </ul>
      <a class="btn" href="/blog">See every list</a>
    </section>
    {HOME_END}"""
    if HOME_START in text:
        text = re.sub(re.escape(HOME_START) + r".*?" + re.escape(HOME_END), lambda _: block, text, flags=re.S)
    else:
        anchor = re.search(r'\n(\s*)<section[^>]*id="faq"', text)
        if not anchor:
            print("homepage: FAQ section not found - latest posts not added"); return
        text = text[:anchor.start()] + "\n    " + block + text[anchor.start():]
    p.write_text(text)


def key():
    if not KEY_FILE.exists():
        import secrets
        KEY_FILE.write_text(secrets.token_hex(16))
    k = KEY_FILE.read_text().strip()
    (ROOT / f"{k}.txt").write_text(k)          # served from the site root
    return k


def ping(urls):
    urls = [u if u.startswith("http") else SITE + u for u in urls]
    body = json.dumps({"host": "linkker.space", "key": key(), "keyLocation": f"{SITE}/{key()}.txt",
                       "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"indexnow: {r.status} for {len(urls)} url(s)")
    except urllib.error.HTTPError as e:
        print(f"indexnow: HTTP {e.code} {e.reason} for {len(urls)} url(s)")
    except Exception as e:
        print(f"indexnow: failed ({type(e).__name__}: {e})")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        ps = posts()
        write_feed(ps); write_llms(ps); write_homepage(ps); key()
        print(f"feed.xml + llms.txt + homepage: {len(ps)} articles")
    elif cmd == "ping":
        ping(sys.argv[2:])
    elif cmd == "ping-all":
        ping(re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text()) + [f"{SITE}/blog/feed.xml"])
