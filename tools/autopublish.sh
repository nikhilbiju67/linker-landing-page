#!/bin/sh
# Publish the oldest draft that passes the quality gate, unattended. One per run.
#
# The timer fires at a fixed time, so the jitter lives here: a random wait of up
# to MAX_JITTER_MIN first. Drafts that fail the gate move to content/held/ with
# their reasons instead of going live.
#
# Disable without touching the timer: tools/blog auto off
set -e
export PATH="$HOME/.local/bin:$HOME/bin:$HOME/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p content/logs content/held
LOG="$ROOT/content/logs/autopublish.log"
MAX_JITTER_MIN=${MAX_JITTER_MIN:-90}

say() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }
# Telegram on the server (tgnotify, the Hermes bot), notification centre on the Mac.
notify() {
  [ -x "$HOME/bin/tgnotify" ] && "$HOME/bin/tgnotify" "Linkker blog" "$1"
  osascript -e "display notification \"$1\" with title \"Linkker blog\"" 2>/dev/null || true
}
waiting() { ls content/drafts/*.md 2>/dev/null | grep -v '/_' || true; }

[ -f content/.autopublish-off ] && { say "skipped: switched off"; exit 0; }

generating() { pgrep -f "$ROOT/tools/generate.py" >/dev/null 2>&1; }
wait_for_generate() { n=0; while generating && [ $n -lt 90 ]; do sleep 30; n=$((n+1)); done; }
sleep "${START_DELAY_S:-60}"
wait_for_generate
if [ -z "$(waiting)" ] && ! grep -q "^=== $(date +%F) blog new" content/logs/generate.log 2>/dev/null; then
  say "no draft and no generate today - generating now"
  "$ROOT/tools/blog" new >> content/logs/generate.log 2>> content/logs/generate.err || say "generate failed"
fi
[ -z "$(waiting)" ] && { say "nothing waiting"; exit 0; }

if [ "$MAX_JITTER_MIN" -gt 0 ]; then
  JITTER=$(awk -v m="$MAX_JITTER_MIN" 'BEGIN{srand();print int(rand()*m*60)}')
  say "waiting ${JITTER}s before publishing"
  sleep "$JITTER"
fi
[ -f content/.autopublish-off ] && { say "switched off during the wait - nothing published"; exit 0; }
[ -z "$(waiting)" ] && { say "nothing left to publish"; exit 0; }
wait_for_generate

for f in $(waiting); do
  n=$(basename "$f" .md)
  if ! REASONS=$(python3 tools/check_draft.py "$f" --links); then
    mv "$f" content/held/
    echo "$REASONS" > "content/held/$n.reasons.txt"
    say "held $n:"; echo "$REASONS" >> "$LOG"
    notify "Held back: $n (failed checks - tools/blog held)"
  fi
done
NEXT=$(ls -tr content/drafts/*.md 2>/dev/null | grep -v '/_' | head -1 || true)
[ -z "$NEXT" ] && { say "nothing passed the checks"; exit 0; }
SLUG=$(basename "$NEXT" .md)

say "publishing: $SLUG"
if FORCE=1 "$ROOT/tools/publish.sh" "$SLUG" >> "$LOG" 2>&1; then
  say "done: $SLUG"
  notify "Published: https://linkker.space/blog/$SLUG"
else
  say "FAILED: $SLUG (see above)"
  notify "Auto-publish failed for $SLUG - see content/logs/autopublish.log"
  exit 1
fi
