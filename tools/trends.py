#!/usr/bin/env python3
"""Find what people are searching for in "best free sites / tools" land right now.

Google autocomplete, no API key: suggestions come back ordered by how often they
are searched, so they read current demand in the searcher's own words. Only
list-shaped, tool-shaped queries survive the filters.

Prints JSON: ranked candidates with related searches. Caches content/trends.json.
"""
import datetime, json, re, sys, time, urllib.parse, urllib.request

from common import ROOT, entries, POSTS, DRAFTS, HELD, words

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Linkker-blog/1.0"}
REGIONS = ["us", "in"]

SEEDS = [
    "best free websites for", "best websites for", "useful websites for", "cool websites",
    "free ai tools for", "best ai tools for", "best free ai", "free ai", "ai tool to",
    "free online tool to", "free website to", "websites like", "free alternative to",
    "alternative to", "best chrome extensions for", "free tools for", "best free tools for",
    "how to remove", "how to compress", "how to convert", "how to make a free",
    "free image", "free video editor", "free pdf", "free online", "sites to learn",
    "best free apps for", "pocket alternative", "bookmark manager", "read it later",
    "how to save links", "how to organize bookmarks", "free stock", "free resume",
]

TOOLISH = re.compile(r"\b(websites?|sites?|tools?|apps?|ai|extensions?|online|software|"
                     r"generators?|editors?|converters?|makers?|builders?|bookmarks?|pdf|images?|"
                     r"photos?|videos?|background|compress\w*|resume|stock (photos?|images?|videos?)|fonts?|"
                     r"icons?|whiteboard|notes?|read(ing)? later|links?)\b", re.I)
# "alternative to X" / "websites like X" only when X is software people actually pay for or use daily.
COMPARE = re.compile(r"\b(like|alternatives?|instead of)\b", re.I)
SOFTWARE = re.compile(r"\b(photoshop|lightroom|illustrator|premiere|after effects|acrobat|adobe|canva|figma|"
                      r"grammarly|notion|evernote|onenote|chatgpt|claude|gemini|copilot|midjourney|capcut|"
                      r"spotify|microsoft (word|excel|office|powerpoint)|word|excel|powerpoint|office|"
                      r"google (docs|drive|sheets|slides|keep)|dropbox|zoom|slack|trello|asana|todoist|"
                      r"duolingo|quizlet|pocket|raindrop|instapaper|final cut|davinci|filmora|imovie|"
                      r"wix|squarespace|wordpress|mailchimp|calendly|loom|miro|zapier|ilovepdf|smallpdf|"
                      r"remove\.bg|pinterest|unsplash|shutterstock|freepik|chegg|coursera|udemy)\b", re.I)
LISTY = re.compile(r"\b(best|top|free|alternatives?|like|sites|websites|tools|apps|extensions|"
                   r"how to)\b", re.I)
# Not for this blog: piracy, adult, navigational and brand-login queries, jobs, gambling.
NOPE = re.compile(r"\b(movies?|watch|stream(ing)?|anime|manga|torrents?|pirat\w*|crack(ed)?|keygen|"
                  r"apk|mod|unblocked|proxy|vpn free|hack(s|ing)?|cheats?|porn\w*|nsfw|adult|nude\w*|"
                  r"sex\w*|onlyfans|dating|casino|bet(ting)?|gambl\w*|crypto|bitcoin|forex|loan|"
                  r"login|log in|sign ?in|sign ?up|download (youtube|instagram|tiktok)|"
                  r"youtube (to|downloader)|near me|jobs?|salary|stock market|shares?|price of|"
                  r"essay writer|homework answers|do my homework|answer key|bypass|undetectable|omegle|"
                  r"strangers?|games?|gaming|zelda|awakening|minecraft|roblox|fortnite|celsius|fahrenheit|inches|cm|kg|lbs|feet|currency|dollars?|rupees?)\b", re.I)


def get(url, timeout=8):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def suggest(q, gl):
    url = ("https://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl="
           f"{gl}&q={urllib.parse.quote(q + ' ')}")
    try:
        return json.loads(get(url))[1]
    except Exception:
        return []


def covered():
    out = []
    for f, fm in entries(POSTS, DRAFTS, HELD):
        out += [words(fm.get("title", "")), words(fm.get("targetQuery", "")), words(f.stem.replace("-", " "))]
    return out


def too_close(ws, done, limit=.5):
    return any(ws and d and len(ws & d) / len(ws | d) >= limit for d in done)


def fmt_for(q):
    q = q.lower()
    if re.search(r"\b(bookmarks?|read(ing)? later|pocket|save links?|saving links|organi[sz]e links?)\b", q):
        return "linkker-guide"
    if re.search(r"\b(alternatives?|instead of|like)\b", q):
        return "alternatives"
    if re.match(r"^how to\b", q) or re.search(r"\b(ai tool to|tool to|website to)\b", q):
        return "how-to-tools"
    if re.search(r"\b(cool|fun|useful|weird|interesting) (websites|sites)\b", q):
        return "hidden-gems"
    if re.search(r"\bfor (students|teachers|designers|developers|freelancers|writers|creators|"
                 r"small business(es)?|marketers|kids|programmers)\b", q):
        return "starter-kit"
    return "top-list"


def main():
    done = covered()
    cand = {}
    for gl in REGIONS:
        for seed in SEEDS:
            for rank, s in enumerate(suggest(seed, gl)):
                s = s.strip().lower()
                if len(s.split()) < 3 or not TOOLISH.search(s) or NOPE.search(s):
                    if not (COMPARE.search(s) and SOFTWARE.search(s) and not NOPE.search(s)):
                        continue
                if COMPARE.search(s) and not SOFTWARE.search(s):
                    continue
                c = cand.setdefault(s, {"query": s, "score": 0.0, "regions": set(), "seed": seed})
                c["score"] = max(c["score"], 10 - rank)
                c["regions"].add(gl)
            time.sleep(.25)                       # be polite to the endpoint

    ranked = []
    for c in cand.values():
        ws = words(c["query"])
        if not ws or too_close(ws, done):
            continue
        s = c["score"]
        if LISTY.search(c["query"]):
            s += 3                                 # list-shaped: what this blog does best
        if len(c["regions"]) > 1:
            s += 2                                 # asked in the US AND India
        if 3 <= len(c["query"].split()) <= 8:
            s += 1
        related = sorted((o["query"] for o in cand.values()
                          if o is not c and len(words(o["query"]) & ws) >= 1
                          and len(words(o["query"]) & ws) / max(1, len(ws)) >= .5), key=len)[:8]
        ranked.append({"query": c["query"], "score": round(s, 1), "regions": sorted(c["regions"]),
                       "seed": c["seed"], "format": fmt_for(c["query"]), "related": related})
    ranked.sort(key=lambda r: -r["score"])
    out = {"pulled": datetime.datetime.now().isoformat(timespec="minutes"), "candidates": ranked[:30]}
    (ROOT / "content" / "trends.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    sys.exit(main())
