#!/usr/bin/env python3
"""Generate one draft list article with Codex (web search on), verify every link,
fetch each site's icon, and render the cover image.

Writes content/drafts/<slug>.md - never straight into the published folder. The
evening auto-publish job runs tools/check_draft.py on it before it goes live.
"""
import datetime, json, re, subprocess, sys, time, urllib.parse

from common import ROOT, DRAFTS, ASSETS, FAV, CODEX, entries, POSTS, write_post
from linkcheck import check, fav

SCHEMA = ROOT / "tools" / "schema.json"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def items_range(fmt):
    m = re.search(rf"^## {re.escape(fmt)}$\s*Length (\d+)-(\d+) words\. Items (\d+)-(\d+)\.",
                  (ROOT / "content" / "formats.md").read_text(), re.M)
    return (int(m.group(3)), int(m.group(4))) if m else (6, 10)


def spec(fmt):
    m = re.search(rf"^## {re.escape(fmt)}$(.*?)(?=^---|\Z)", (ROOT / "content" / "formats.md").read_text(), re.S | re.M)
    return f"FORMAT: {fmt}\n{m.group(1).strip()}" if m else f"FORMAT: {fmt}"


def published(limit=15):
    es = sorted(entries(POSTS), key=lambda e: e[0].stat().st_mtime, reverse=True)[:limit]
    return "\n".join(f'- "{fm["title"]}" -> /blog/{f.stem}/' for f, fm in es)


def codex(prompt, schema=None, timeout=1800):
    cmd = [CODEX, "--search", "exec", "--skip-git-repo-check", "-s", "read-only", "--ephemeral"]
    if schema:
        cmd += ["--output-schema", str(schema)]
    for attempt in (1, 2):
        try:
            r = run(cmd + [prompt], timeout=timeout, cwd=str(ROOT))
            if r.returncode == 0:
                return r.stdout
            print(f"codex failed (attempt {attempt}): {r.stderr[-300:]}", flush=True)
        except subprocess.TimeoutExpired:
            print(f"codex timed out (attempt {attempt})", flush=True)
        time.sleep(30)
    return None


def last_json(text, keys):
    for b in reversed(re.findall(r"\{[\s\S]*\}", text or "")):
        try:
            d = json.loads(b)
            if keys <= d.keys():
                return d
        except Exception:
            continue
    return None


def domain(url):
    return (urllib.parse.urlparse(url).hostname or "").removeprefix("www.")


def verify(items, report):
    """Keep items whose link is live; one item per site."""
    out, seen = [], set()
    for it in items:
        it["url"] = it["url"].strip()
        d = domain(it["url"])
        if d in seen:
            report.append(f"dropped {it['name']}: duplicate site {d}"); continue
        r = check(it["url"])
        if not r["ok"]:
            report.append(f"dropped {it['name']} ({it['url']}): {r['reason']}"); continue
        seen.add(d)
        out.append(it)
    return out


def main():
    DRAFTS.mkdir(parents=True, exist_ok=True); FAV.mkdir(parents=True, exist_ok=True)
    pick = json.loads(run([sys.executable, str(ROOT / "tools" / "pick_topic.py")], timeout=1200).stdout)
    if "error" in pick:
        print("no topic available:", pick["error"]); return 3
    fmt = pick["format"]
    lo, hi = items_range(fmt)
    voice = (ROOT / "content" / "voice.md").read_text()
    ev = pick.get("evidence")
    evidence = (f"\nSEARCH CONSOLE SIGNAL: Google already shows linkker.space {ev['impressions']} times for this "
                f"query at average position {ev['position']} with {ev['clicks']} clicks. Beat what outranks us.\n"
                if ev else "")
    related = pick.get("related") or []
    also = ("\nPEOPLE ALSO SEARCH (live Google suggestions). Answer the ones that genuinely fit, in the "
            "outro's Quick answers or inside an item, in the searcher's own words:\n"
            + "\n".join(f"- {q}" for q in related) + "\n") if related else ""
    links = published()
    links = ("\nEXISTING ARTICLES: where one genuinely relates, link it once from the intro or outro as an "
             "ordinary markdown link on a natural phrase. Skip any that do not fit:\n" + links + "\n") if links else ""

    prompt = f"""{voice}

---

Write ONE list article for the Linkker blog (linkker.space/blog).

TARGET QUERY: {pick['query']}
WORKING TITLE: {pick.get('title') or '(choose one)'}
ANGLE: {pick['angle']}{evidence}{also}
{spec(fmt)}

Use web search to confirm, for every site you list: that it exists today, its exact official https URL,
that the job described is genuinely free, and what the catch is. List {lo}-{hi} sites (aim for {hi},
some may be dropped by a link check). Order follows the format above.
Today is {datetime.date.today():%d %B %Y}; say nothing that will date badly, such as "this year".
The quick-picks box and the call-to-action are added automatically: do not write either.
{links}
Respond ONLY with the JSON object matching the schema."""

    print(f"generating: {pick['slug']} ({fmt}, source {pick['source']}) …", flush=True)
    art = last_json(codex(prompt, SCHEMA), {"title", "items", "intro", "outro"})
    if not art:
        print("could not get an article from codex"); return 1

    report = []
    items = verify(art["items"], report)
    if len(items) < lo:
        need = hi - len(items)
        print(f"only {len(items)} live items, asking for {need} more …", flush=True)
        have = ", ".join(f"{i['name']} ({i['url']})" for i in items)
        bad = "; ".join(report)
        more = last_json(codex(
            f"{voice}\n---\nThe list article '{art['title']}' (target query: {pick['query']}) needs {need} more "
            f"items. Already listed: {have}. These failed a live link check: {bad}. Use web search to find "
            f"{need} other genuinely free, reputable sites for the same job, with exact official https URLs. "
            'Reply ONLY with JSON: {"items": [ {"name","url","oneLiner","body","bestFor","price","catch"} ]} '
            "using the same field rules as before (price is one of Free, Free plan, Free & open source, Free with ads).",
            timeout=1200), {"items"})
        if more:
            items += verify([i for i in more["items"] if isinstance(i, dict) and i.get("url")], report)
    items = items[:hi]
    for line in report:
        print("  " + line)
    if len(items) < lo:
        print(f"only {len(items)} items survived the link check ({lo} needed) - no draft today"); return 1

    for it in items:
        d = domain(it["url"])
        it["fav"] = f"{d}.png" if (FAV / f"{d}.png").exists() or fav(d, FAV / f"{d}.png") else ""
        it["checked"] = datetime.date.today().isoformat()

    for k in ("title", "description"):
        art[k] = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", art[k]).strip()
    art["title"] = re.sub(r"[\s:\u2013\u2014-]+$", "", art["title"])
    # The title promised N items; keep it honest after the link check.
    art["title"] = re.sub(r"^\d+(?=\s)", str(len(items)), art["title"])

    s = pick["slug"]
    hero = ASSETS / f"{s}.jpg"
    h = run(["node", str(ROOT / "tools" / "hero.mjs"), json.dumps({
        "out": str(hero), "title": art["title"], "kicker": pick["kicker"], "note": art.get("heroLine", ""),
        "count": len(items), "sites": [{"domain": domain(i["url"]),
                                        "fav": str(FAV / i["fav"]) if i["fav"] else ""} for i in items[:4]]})],
            timeout=180)
    print((h.stdout or h.stderr).strip()[-300:])

    names = ", ".join(i["name"] for i in items[:3])
    fm = {
        "title": art["title"], "description": art["description"], "date": datetime.date.today().isoformat(),
        "hero": f"/assets/{s}.jpg",
        "heroAlt": f"Cover illustration: {art['title']}, with link cards for {names}",
        "readingTime": art.get("readingTime", 6), "targetQuery": pick["query"], "kicker": pick["kicker"],
        "format": fmt, "source": pick["source"], "items": items,
    }
    write_post(DRAFTS / f"{s}.md", fm, f"{art['intro'].strip()}\n\n<!-- picks -->\n\n{art['outro'].strip()}")
    print(f"draft ready: content/drafts/{s}.md ({len(items)} sites)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
