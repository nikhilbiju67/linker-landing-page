#!/usr/bin/env python3
"""Automatic quality gate for a draft list article.

    check_draft.py <draft.md> [--links]   exit 0 = publish, exit 1 = hold (reasons printed)

Catches what would embarrass the blog: broken front matter, too few sites, a dead
or duplicated link (--links re-checks every URL live, which the publish job does),
banned phrases, prices, emoji, exclamation marks, NSFW or shady topics, a missing
cover, too many Linkker mentions, or a topic that duplicates a live post.
"""
import re, sys

from common import ROOT, POSTS, front, entries, similar

SHADY = re.compile(r"\b(nsfw|porn\w*|nude\w*|onlyfans|torrent\w*|pira(te|cy)|cracked|keygen|warez|"
                   r"unblocked|casino|gambling|betting|apk mirror)\b", re.I)


def ranges(fmt):
    m = re.search(rf"^## {re.escape(fmt)}$\s*Length (\d+)-(\d+) words\. Items (\d+)-(\d+)\.",
                  (ROOT / "content" / "formats.md").read_text(), re.M)
    return tuple(map(int, m.groups())) if m else (600, 1900, 5, 12)


def banned():
    v = (ROOT / "content" / "voice.md").read_text()
    m = re.search(r"Never use:(.*?)\n- ", v, re.S)
    return [p.lower() for p in re.findall(r'"([^"]+)"', m.group(1))] if m else []


def main(path, live_links=False):
    text = open(path, errors="ignore").read()
    fm, body = front(text)
    if not fm:
        return ["no front matter"]
    bad = []
    title, desc, fmt = fm.get("title", ""), fm.get("description", ""), fm.get("format", "top-list")
    items = fm.get("items") or []
    wlo, whi, ilo, ihi = ranges(fmt)
    if not 20 <= len(title) <= 72:
        bad.append(f"title length {len(title)}")
    if not 70 <= len(desc) <= 170:
        bad.append(f"description length {len(desc)}")
    if "<!-- picks -->" not in body:
        bad.append("body has no <!-- picks --> marker")
    if not ilo <= len(items) <= ihi + 2:
        bad.append(f"{len(items)} items, {fmt} wants {ilo}-{ihi}")
    m = re.match(r"^(\d+)\s", title)
    if m and int(m.group(1)) != len(items):
        bad.append(f"title promises {m.group(1)} but lists {len(items)}")

    hosts = []
    for i, it in enumerate(items, 1):
        for k in ("name", "url", "oneLiner", "body", "bestFor"):
            if not str(it.get(k, "")).strip():
                bad.append(f"item {i} has no {k}")
        url = it.get("url", "")
        if not url.startswith("https://"):
            bad.append(f"item {i} url is not https: {url}")
        h = re.sub(r"^www\.", "", re.sub(r"^https://([^/]+).*$", r"\1", url).lower())
        if h in hosts:
            bad.append(f"item {i} repeats {h}")
        hosts.append(h)

    prose = "\n".join([body] + [f"{it.get('oneLiner','')}\n{it.get('body','')}\n{it.get('bestFor','')}\n"
                                f"{it.get('catch','')}" for it in items])
    n = len(re.findall(r"\b\w+\b", prose))
    if not wlo * .7 <= n <= whi * 1.35:
        bad.append(f"{n} words, {fmt} wants {wlo}-{whi}")
    low = prose.lower()
    hits = [b for b in banned() if b in low]
    if hits:
        bad.append("banned phrases: " + ", ".join(hits))
    # A "!" that belongs to a listed site's own name ("Quick, Draw!") is not hype.
    unnamed = prose
    for nm in {it.get("name", "") for it in items if "!" in it.get("name", "")}:
        unnamed = unnamed.replace(nm, "")
    if "!" in re.sub(r"!\[[^\]]*\]\([^)]*\)|<!--.*?-->", "", unnamed, flags=re.S):
        bad.append("exclamation mark")
    # A soft hyphen or zero-width character usually marks a title the writer cut short.
    if re.search(r"[­​-‏⁠﻿]", "\n".join([title, desc, prose])):
        bad.append("invisible character (soft hyphen or zero-width) - text may be cut off")
    if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", prose):
        bad.append("emoji")
    if re.search(r"[$€£₹¥]\s?\d|\b\d+(\.\d+)?\s?(usd|dollars?|rupees?|euros?)\b|/\s?mo(nth)?\b", low):
        bad.append("quotes a price")
    if SHADY.search(prose + " " + title):
        bad.append("shady or NSFW topic: " + SHADY.search(prose + " " + title).group(0))
    if re.search(r"\bTODO\b|(?i:\b(lorem ipsum|as an ai|\[insert))", prose):
        bad.append("placeholder text")
    mentions = len(re.findall(r"\blinkker\b", body, re.I))
    if mentions > (3 if fmt == "linkker-guide" else 1):
        bad.append(f"mentions Linkker {mentions} times in the body")
    hero = ROOT / "blog-src" / fm.get("hero", "").lstrip("/")
    if not hero.exists():
        bad.append("cover image missing")

    me = path.rsplit("/", 1)[-1][:-3]
    for f, other in entries(POSTS):
        if f.stem != me and (similar(title, other.get("title", "")) >= .6
                             or similar(fm.get("targetQuery", ""), other.get("targetQuery", "")) >= .7):
            bad.append(f"duplicates live post {f.stem}"); break

    if live_links:
        from linkcheck import check
        for i, it in enumerate(items, 1):
            r = check(it.get("url", ""))
            if not r["ok"]:
                bad.append(f"item {i} ({it.get('name')}) link failed: {r['reason']}")
    return bad


if __name__ == "__main__":
    problems = main(sys.argv[1], "--links" in sys.argv)
    for b in problems:
        print(f"  - {b}")
    sys.exit(1 if problems else 0)
