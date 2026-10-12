#!/usr/bin/env python3
"""Check that a listed site is real, live and safe to send readers to.

    linkcheck.py <url> [<url> ...]     prints OK/FAIL per url; exit code = failures

A list post is only as good as its links: every item URL must be https, answer
with a page (not a parked domain or an error), and stay on the same site after
redirects. Sites behind a bot challenge (Cloudflare 403/503) count as live.
Also fetches each site's favicon for the item card (fav()).
"""
import re, sys, urllib.error, urllib.parse, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
PARKED = re.compile(r"(domain (is )?for sale|buy this domain|parked (free|domain)|this domain may be for sale|"
                    r"hugedomains|\bsedo\b|dan\.com|domain has expired|account suspended|site not found|"
                    r"404 not found|page not found)", re.I)


def base(host):
    parts = (host or "").lower().split(".")
    return ".".join(parts[-3:]) if len(parts) > 2 and len(parts[-2]) <= 3 else ".".join(parts[-2:])


def check(url):
    res = {"url": url, "ok": False, "status": None, "final": None, "title": "", "reason": ""}
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or not u.netloc:
        res["reason"] = "not an https url"; return res
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8",
                                               "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res["status"], res["final"] = r.status, r.geturl()
            page = r.read(300_000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        res["status"], res["final"] = e.code, url
        hdrs = {k.lower(): v for k, v in (e.headers or {}).items()}
        if e.code in (403, 429, 503) and ("cf-ray" in hdrs or "cloudflare" in hdrs.get("server", "").lower()
                                          or "akamai" in hdrs.get("server", "").lower()):
            res.update(ok=True, reason="live behind a bot check"); return res
        res["reason"] = f"HTTP {e.code}"; return res
    except Exception as e:
        res["reason"] = f"{type(e).__name__}: {e}"[:120]; return res
    m = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
    res["title"] = re.sub(r"\s+", " ", m.group(1)).strip()[:120] if m else ""
    fin = urllib.parse.urlparse(res["final"])
    if fin.scheme != "https":
        res["reason"] = "redirects to plain http"; return res
    if base(fin.hostname) != base(u.hostname):
        res["reason"] = f"redirects to another site ({fin.hostname})"; return res
    if PARKED.search(res["title"]) or (len(page) < 600 and "<script" not in page.lower()):
        res["reason"] = f"looks parked or empty ({res['title'] or 'no title'})"; return res
    res["ok"] = True
    return res


def fav(domain, dest):
    """Save the site's icon (via Google's favicon service) to dest. True if it worked."""
    url = f"https://www.google.com/s2/favicons?domain={urllib.parse.quote(domain)}&sz=128"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=15) as r:
            data = r.read()
        if len(data) < 300 or not data.startswith(b"\x89PNG"):
            return False                      # the generic globe, or not an image
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    bad = 0
    for url in sys.argv[1:]:
        r = check(url)
        bad += not r["ok"]
        print(f"{'OK  ' if r['ok'] else 'FAIL'} {url}  {r['status']}  {r['title'] or r['reason']}"
              + (f"  ({r['reason']})" if r["ok"] and r["reason"] else ""))
    sys.exit(bad)
