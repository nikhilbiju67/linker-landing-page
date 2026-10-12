#!/usr/bin/env python3
"""Search Console queries for linkker.space.

    gsc.py            JSON: rows pulled + ranked "opportunities"
                      (queries Google already shows us for, at a weak position)

Auth: gcloud application-default credentials with the webmasters scope (the same
login the JustThen and Claryzo pipelines use), or the ADC file directly when gcloud
is not installed (the Linux server).
"""
import datetime, json, pathlib, subprocess, sys, urllib.parse, urllib.request

SITE = "https://linkker.space/"
QUOTA_PROJECT = "malayali-dating"   # has searchconsole.googleapis.com enabled
API = "https://searchconsole.googleapis.com/webmasters/v3/sites/{}/searchAnalytics/query"
BRAND = ("linkker", "linker", "link ker")


def token():
    for cmd in (["gcloud", "auth", "application-default", "print-access-token"],
                ["/opt/homebrew/bin/gcloud", "auth", "application-default", "print-access-token"]):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
        except Exception:
            continue
    adc = pathlib.Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    if adc.exists():
        c = json.loads(adc.read_text())
        body = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["client_secret"],
                                       "refresh_token": c["refresh_token"],
                                       "grant_type": "refresh_token"}).encode()
        with urllib.request.urlopen("https://oauth2.googleapis.com/token", body, timeout=30) as r:
            return json.load(r)["access_token"]
    raise SystemExit("gcloud not found or ADC not configured")


def query(days=28, dimensions=("query",), limit=500):
    end = datetime.date.today() - datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=days)
    body = json.dumps({"startDate": start.isoformat(), "endDate": end.isoformat(),
                       "dimensions": list(dimensions), "rowLimit": limit}).encode()
    req = urllib.request.Request(
        API.format(urllib.parse.quote(SITE, safe="")), data=body,
        headers={"Authorization": f"Bearer {token()}", "x-goog-user-project": QUOTA_PROJECT,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r).get("rows", [])


def is_brand(q):
    q = q.lower()
    return any(b in q for b in BRAND)


def opportunities(rows):
    out = []
    for r in rows:
        q = r["keys"][0]
        if is_brand(q):
            continue
        imp, clicks, pos = r.get("impressions", 0), r.get("clicks", 0), r.get("position", 100)
        # Impressions at a weak position is the definition of an unclaimed win.
        score = imp * (1 if pos > 8 else 0.25) * (2 if clicks == 0 else 1)
        out.append({"query": q, "impressions": imp, "clicks": clicks,
                    "position": round(pos, 1), "score": round(score, 1)})
    return sorted(out, key=lambda x: -x["score"])


if __name__ == "__main__":
    try:
        rows = query()
    except Exception as e:
        print(json.dumps({"error": str(e), "rows": 0, "opportunities": []}, indent=2)); sys.exit(0)
    print(json.dumps({
        "pulled": datetime.date.today().isoformat(),
        "rows": len(rows),
        "impressions": sum(r.get("impressions", 0) for r in rows),
        "clicks": sum(r.get("clicks", 0) for r in rows),
        "brand_impressions": sum(r.get("impressions", 0) for r in rows if is_brand(r["keys"][0])),
        "opportunities": opportunities(rows)[:25],
    }, indent=2))
