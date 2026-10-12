#!/usr/bin/env python3
"""Choose the next article: what to write, and in which format.

Priority:
  1. Search Console - a query already earning impressions at a weak position is a
                      page Google wants to rank and cannot yet. Cheapest win.
  2. Google demand  - live autocomplete for list-shaped "best free X" searches
                      (trends.py), in the searcher's own words.
  3. Discovery      - every other day, Codex searches the web for what tools and
                      sites people are talking about this week (fresh angles).
  4. Backlog        - content/backlog.json, hand-ordered.

Formats rotate so the blog never reads as one template, and "linkker-guide" posts
(where Linkker itself fits) stay at most one in five.
"""
import datetime, json, re, subprocess, sys

from common import ROOT, POSTS, DRAFTS, CODEX, FORMATS, entries, slug, taken, words, similar


def log(msg):
    print(f"pick_topic: {msg}", file=sys.stderr)


def recent(n=5):
    """Formats of the n newest posts AND drafts, newest first (drafts must count)."""
    es = sorted(entries(POSTS, DRAFTS), key=lambda e: e[0].stat().st_mtime, reverse=True)[:n]
    return [fm.get("format") for _, fm in es]


def covered(q):
    """Already written (or queued) something close enough to this query."""
    for f, fm in entries(POSTS, DRAFTS):
        if max(similar(q, fm.get("targetQuery", "")), similar(q, fm.get("title", ""))) >= .5:
            return True
    return slug(q) in taken()


def allowed(fmt):
    r = recent()
    if fmt == "linkker-guide" and "linkker-guide" in r:
        return False
    if fmt != "top-list" and r[:1] == [fmt]:
        return False                      # top-list may repeat once; the rest may not
    if fmt == "top-list" and r[:2] == ["top-list", "top-list"]:
        return False
    return True


def from_gsc():
    try:
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "gsc.py")],
                           capture_output=True, text=True, timeout=90)
        data = json.loads(r.stdout)
    except Exception as e:
        log(f"search console unavailable ({type(e).__name__}: {e})"); return None
    if data.get("error"):
        log(f"search console error: {data['error']}"); return None
    opps = [o for o in data.get("opportunities", []) if o["impressions"] >= 3]
    if not opps:
        log(f"search console: {data.get('rows', 0)} rows, {data.get('impressions', 0)} impressions, "
            "no usable opportunities yet"); return None
    for o in opps:
        if covered(o["query"]):
            continue
        from trends import fmt_for
        fmt = fmt_for(o["query"])
        log(f"picked {o['query']!r} from search console ({o['impressions']} impressions, position {o['position']})")
        return {"query": o["query"], "title": None, "format": fmt, "source": "search-console",
                "angle": (f"Google already shows linkker.space for this ({o['impressions']} impressions, "
                          f"average position {o['position']}) but too low to earn the click. Write the page "
                          "that deserves the top spot."), "evidence": o}
    log(f"{len(opps)} search console opportunities, all covered already")
    return None


def from_trends():
    try:
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "trends.py")],
                           capture_output=True, text=True, timeout=300)
        data = json.loads(r.stdout)
    except Exception as e:
        log(f"google demand unavailable ({type(e).__name__}: {e})"); return None
    for c in data.get("candidates", []):
        if covered(c["query"]) or not allowed(c["format"]):
            continue
        log(f"picked {c['query']!r} from google autocomplete (score {c['score']}, {'/'.join(c['regions'])})")
        return {"query": c["query"], "title": None, "format": c["format"], "related": c["related"],
                "source": "google-autocomplete",
                "angle": ("People are typing this into Google right now. Write the list that deserves to "
                          "rank first: more current, more specific and more honest about each site's catch "
                          "than what ranks today.")}
    log("google demand: nothing new and allowed")
    return None


def from_discovery():
    used = "; ".join(fm.get("title", "") for _, fm in entries(POSTS, DRAFTS)) or "nothing yet"
    prompt = (
        "Search the web for free websites, web apps and AI tools that people are actively searching for "
        "and talking about this week (launches, viral tools, seasonal needs such as exams, tax season, "
        "holidays). Propose ONE list article for a blog about useful websites, in the form 'the best free "
        "<kind of site> for <job>'. It must be safe and legal (no piracy, adult content, gambling or "
        "crypto) and useful to a general audience.\n\nAlready covered, do not repeat: " + used + "\n\n"
        "Formats: " + ", ".join(f for f in FORMATS if f != "linkker-guide") + ".\n"
        'Reply with ONLY a JSON object: {"title": "...", "query": "the phrase someone would type into '
        'Google", "format": "one of the formats", "angle": "one sentence on why now and the specific take"}')
    try:
        r = subprocess.run([CODEX, "--search", "exec", "--skip-git-repo-check", "-s", "read-only",
                            "--ephemeral", prompt], capture_output=True, text=True, timeout=900)
    except Exception as e:
        log(f"discovery failed ({type(e).__name__})"); return None
    for blob in reversed(re.findall(r"\{[^{}]*\}", r.stdout)):
        try:
            d = json.loads(blob)
        except Exception:
            continue
        if {"title", "query", "angle"} <= d.keys() and not covered(d["query"]):
            fmt = d.get("format") if d.get("format") in FORMATS else "top-list"
            if not allowed(fmt):
                fmt = "top-list" if allowed("top-list") else "hidden-gems"
            log(f"picked {d['query']!r} from discovery")
            return {**d, "format": fmt, "source": "discovery"}
    log("discovery returned nothing usable")
    return None


def from_backlog():
    for t in json.load(open(ROOT / "content" / "backlog.json"))["topics"]:
        if not covered(t["query"]) and slug(t["title"]) not in taken() and allowed(t["format"]):
            log(f"picked backlog topic {t['title']!r}")
            return {**t, "source": "backlog"}
    for t in json.load(open(ROOT / "content" / "backlog.json"))["topics"]:
        if not covered(t["query"]) and slug(t["title"]) not in taken():
            return {**t, "source": "backlog"}       # rotation rule could not be met; still write
    return None


if __name__ == "__main__":
    odd = datetime.date.today().toordinal() % 2
    order = [from_gsc, from_trends] + ([from_discovery, from_backlog] if odd else [from_backlog, from_discovery])
    pick = None
    for source in order:
        pick = source()
        if pick:
            break
    if not pick:
        print(json.dumps({"error": "no topic available - add to content/backlog.json"})); sys.exit(3)
    pick.setdefault("kicker", {"top-list": "Free tools", "hidden-gems": "Hidden gems", "how-to-tools": "How to",
                               "alternatives": "Alternatives", "starter-kit": "Starter kits",
                               "linkker-guide": "Saving links"}.get(pick["format"], "Linkker picks"))
    if re.search(r"\bai\b", pick["query"]) and pick["format"] in ("top-list", "how-to-tools"):
        pick["kicker"] = "AI tools"
    pick["slug"] = slug(pick.get("title") or pick["query"])
    print(json.dumps(pick, indent=2))
