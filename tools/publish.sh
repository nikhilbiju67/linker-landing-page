#!/bin/sh
# Publish one draft (or rebuild) and push the site live on Vercel.
#   publish.sh <slug|next>     publish that draft (next = oldest waiting)
#   publish.sh rebuild         rebuild + redeploy without a new post
# On the server (BLOG_GIT_PUSH=1) git is the source of truth: pull site edits pushed
# from the Mac first, then commit + push what was published; that push is the deploy.
set -e
export PATH="$HOME/.local/bin:$HOME/bin:$HOME/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p content/logs
[ -z "$1" ] && { echo "usage: publish.sh <slug|next|rebuild>"; exit 2; }

if [ "${BLOG_GIT_PUSH:-0}" = 1 ] && [ -z "${BLOG_PULLED:-}" ]; then
  git pull -q --rebase --autostash || { echo "git pull failed - not publishing"; exit 1; }
  # The pull may have replaced this very script mid-run; start again from the new copy.
  BLOG_PULLED=1 exec sh "$ROOT/tools/publish.sh" "$@"
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

deploy_failed() {
  restore; rm -rf blog; npx @11ty/eleventy --quiet >/dev/null 2>&1 || true
  python3 tools/sitemap.py >/dev/null; python3 tools/discover.py build >/dev/null
  echo "DEPLOY FAILED - draft restored"; exit 1
}

if [ "${BLOG_GIT_PUSH:-0}" = 1 ]; then
  # Server: the push to main is the deploy (Vercel's GitHub integration builds production
  # from every push), so no Vercel login is needed here. The CLI login copied from the Mac
  # failed every evening: its 8-hour token had always expired by then, and CLI 63 refreshes
  # it but goes on calling the API with the revoked one ("Not authorized").
  BEFORE=$(git rev-parse HEAD)
  git add -A
  if git commit -q -m "blog: ${SLUG:-rebuild}"; then
    git push -q || { git reset -q "$BEFORE"; echo "git push failed"; deploy_failed; }
  fi
  if [ -n "$SLUG" ]; then
    # Vercel serves a push within seconds; wait for the post before pinging search engines.
    n=0
    until [ "$(curl -s -o /dev/null -w '%{http_code}' "https://linkker.space/blog/$SLUG")" = 200 ]; do
      n=$((n+1))
      [ $n -gt 30 ] && { echo "pushed, but /blog/$SLUG is not live after 5 min - check the Vercel deployment"; exit 1; }
      sleep 10
    done
  fi
else
  # Mac: deploy with the CLI. Refresh an expired login in a run of its own first, or the
  # deploy hits the same CLI 63 bug.
  vercel whoami >/dev/null 2>&1 || true
  if ! OUT=$(vercel deploy --prod --yes 2>&1); then
    echo "$OUT" | tail -15; deploy_failed
  fi
  echo "$OUT" | grep -E '^(Production|✅|https://)' | tail -2 || true
fi
echo "live: https://linkker.space/blog${SLUG:+/$SLUG}"

URLS="/ /blog /blog/feed.xml /sitemap.xml /llms.txt"
[ -n "$SLUG" ] && URLS="/blog/$SLUG $URLS"
python3 tools/discover.py ping $URLS || true
