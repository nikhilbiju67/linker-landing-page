# The Linkker blog (linkker.space/blog)

URLs have no trailing slash (`/blog`, `/blog/<slug>`), matching vercel.json `trailingSlash: false`.

Hand-picked lists of free websites and AI tools, generated, checked and published
automatically from the Oracle server (systemd timers, user `opc`).

| When | Job | What happens |
|---|---|---|
| 10:00 daily | `linkker-blog-generate` | `tools/blog new` picks a topic (`pick_topic.py`), Codex researches and writes it with web search, every site's link is checked live (`linkcheck.py`), icons are fetched, the cover is rendered (`hero.mjs`). Draft goes to `content/drafts/`. Skips if 2+ drafts wait. |
| 19:30 to 21:00 | `linkker-blog-publish` | `tools/autopublish.sh` waits 0-90 min, runs the gate (`check_draft.py --links`), publishes the oldest passing draft: Eleventy build, sitemap, feed, llms.txt, homepage block, `vercel deploy --prod`, git commit + push, IndexNow ping. Failing drafts move to `content/held/` with reasons. |

## How a topic is picked
1. **Search Console** (`gsc.py`, property `https://linkker.space/`): a query that already
   gets impressions at a weak position.
2. **Google autocomplete** (`trends.py`): live list-shaped "best free X" searches.
3. **Discovery** (every other day): Codex searches the web for tools people talk about this week.
4. **Backlog** (`content/backlog.json`).

Formats rotate (`content/formats.md`); `linkker-guide` posts stay at most one in five.
The voice and the honesty rules that decide whether a post goes live are in `content/voice.md`.

## Commands
`tools/blog` with no arguments lists them: `new`, `topic`, `trends`, `list`, `check`,
`approve`, `reject`, `held`, `rebuild`, `auto on|off`, `report`.

## Files
- `blog-src/` Eleventy source: templates, `posts/` (published), `assets/` (covers, `fav/` icons)
- `blog/` built output, committed, served as static files by Vercel
- `assets/blog.css` blog styles on top of `assets/site.css`
- `.vercelignore` keeps `blog-src/`, `tools/`, `content/` and node files off the live site

## Editing the site from the Mac
The server commits and pushes every post to `main`. Before editing or deploying from the
Mac: `git pull origin main`; after: push. Otherwise the next server publish overwrites
your edits on the live site.
