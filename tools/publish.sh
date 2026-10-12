#!/bin/sh
# Publish one draft (or rebuild) and push the site live on Vercel.
#   publish.sh <slug|next>     publish that draft (next = oldest waiting)
#   publish.sh rebuild         rebuild + redeploy without a new post
# On the server (BLOG_GIT_PUSH=1) git is the source of truth: pull site edits pushed
# from the Mac first, and commit + push what was published afterwards.
set -e
export PATH="$HOME/.local/bin:$HOME/bin:$HOME/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p content/logs
[ -z "$1" ] && { echo "usage: publish.sh <slug|next|rebuild>"; exit 2; }

if [ "${BLOG_GIT_PUSH:-0}" = 1 ]; then
  git pull -q --rebase --autostash || { echo "git pull failed - not publishing"; exit 1; }
fi

SLUG=""
if [ "$1" != "rebuild" ]; then
  if [ "$1" = "next" ]; then
    DRAFT=$(ls -tr content/drafts/*.md 2>/dev/null | grep -v '/_' | head -1 || true)
    [ -z "$DRAFT" ] && { echo "nothing to publish"; exit 0; }
    SLUG=$(basename "$DRAFT" .md)
  else
    SLUG="$1"; DRAFT="content/drafts/$SLUG.md"
  fi
  [ -f "$DRAFT" ] || { echo "no draft: $DRAFT"; exit 1; }
  [ -e "blog-src/posts/$SLUG.md" ] && { echo "already published: $SLUG"; exit 1; }
  if [ "${FORCE:-0}" != "1" ]; then
    python3 tools/check_draft.py "$DRAFT" --links || { echo "quality gate failed - not publishing (FORCE=1 to override)"; exit 1; }
  fi
  mv "$DRAFT" "blog-src/posts/$SLUG.md"
  echo "approved $SLUG"
fi

restore() { [ -n "$SLUG" ] && mv "blog-src/posts/$SLUG.md" "content/drafts/$SLUG.md" 2>/dev/null; true; }

rm -rf blog
if ! npx @11ty/eleventy --quiet > content/logs/build.log 2>&1; then
  restore; echo "BUILD FAILED - draft restored. Last lines of content/logs/build.log:"; tail -20 content/logs/build.log; exit 1
fi
python3 tools/sitemap.py
python3 tools/discover.py build

if ! OUT=$(vercel deploy --prod --yes 2>&1); then
  echo "$OUT" | tail -15
  restore; rm -rf blog; npx @11ty/eleventy --quiet >/dev/null 2>&1 || true
  python3 tools/sitemap.py >/dev/null; python3 tools/discover.py build >/dev/null
  echo "DEPLOY FAILED - draft restored"; exit 1
fi
echo "$OUT" | grep -E '^(Production|✅|https://)' | tail -2 || true
echo "live: https://linkker.space/blog${SLUG:+/$SLUG}"

if [ "${BLOG_GIT_PUSH:-0}" = 1 ]; then
  git add -A
  git commit -q -m "blog: ${SLUG:-rebuild}" && git push -q \
    || echo "WARNING: git push failed - the site is live but the commit is only on this machine"
fi

URLS="/ /blog /blog/feed.xml /sitemap.xml /llms.txt"
[ -n "$SLUG" ] && URLS="/blog/$SLUG $URLS"
python3 tools/discover.py ping $URLS || true
