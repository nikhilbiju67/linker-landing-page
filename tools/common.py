"""Shared helpers for the Linkker blog pipeline (standard library only)."""
import json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "blog-src" / "posts"
DRAFTS = ROOT / "content" / "drafts"
HELD = ROOT / "content" / "held"
ASSETS = ROOT / "blog-src" / "assets"
FAV = ASSETS / "fav"
SITE = "https://linkker.space"
CODEX = shutil.which("codex") or "/opt/homebrew/bin/codex"
FORMATS = ["top-list", "hidden-gems", "how-to-tools", "alternatives", "starter-kit", "linkker-guide"]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:70].rstrip("-")


def front(text):
    """Front matter is one `key: <json>` per line (valid YAML for Eleventy)."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        try:
            fm[k.strip()] = json.loads(v.strip())
        except Exception:
            fm[k.strip()] = v.strip().strip('"')
    return fm, m.group(2)


def write_post(path, fm, body):
    y = "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in fm.items())
    pathlib.Path(path).write_text(f"---\n{y}\n---\n\n{body.strip()}\n")


def entries(*dirs):
    """(path, front matter) for every post in dirs, skipping _scratch files."""
    out = []
    for d in dirs or (POSTS,):
        for f in sorted(d.glob("*.md")) if d.exists() else []:
            if f.stem.startswith("_"):
                continue
            fm, _ = front(f.read_text(errors="ignore"))
            if fm:
                out.append((f, fm))
    return out


def taken():
    return {f.stem for f, _ in entries(POSTS, DRAFTS, HELD)}


STOP = set("a an the to of in on for and or is it my me i you your with at be do does "
           "how what why when should can are best free top sites site websites website tools "
           "tool online ai app apps".split())


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 2}


def similar(a, b):
    a, b = words(a), words(b)
    return len(a & b) / len(a | b) if a and b else 0.0
