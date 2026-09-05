# soobrosa.info

Daniel Molnar's personal site. Pure static HTML in a black-on-white monospace
theme, built from markdown by a tiny Python script. No Jekyll.

The design is a technical-readout look: system monospace throughout, a hairline
cell grid, uppercase micro-labels, oversized numerals and solid bars. No colour,
no border radius, no shadows, no webfonts — weight, rule and fill carry every
distinction. Press `T` to invert the polarity.

## Structure

```
index.html              Bio / landing page (its counts + bars are build-written)
mixes.html              DJ mix player (reads mixes.json, streams from R2)
words.html              GENERATED: one chronological list of all writing
words/<slug>.html       GENERATED: one page per markdown post
media.html              Talks, interviews and slide decks archive
lab.html                Apps & experiments (reads lab.json)
404.html
atom.xml                GENERATED: Atom feed of the newest 25 entries
redirects.json          Old URL -> new URL, one row per moved page
post/, translation/     GENERATED: redirect stubs for the old Jekyll URLs,
                        plus stubs at the root for retired pages

content/*.md            SOURCE for writing — drop markdown here
build.py                content/*.md -> words/<slug>.html + words.html,
                        plus atom.xml and the redirect stubs, and rewrites
                        index.html's counts + words-by-type bars
migrate.py              One-time importer (old _posts/ + static/ -> content/)

assets/css/site.css     Single shared stylesheet (the whole design)
covers/                 Mix cover art
mixes.json              Mix list (id, title, url, cover)
lab.json                App list (name, blurb, url, external, tech)

.nojekyll               Disables GitHub's default Jekyll build
.github/workflows/      Build + deploy to GitHub Pages on push
Makefile                make build | make serve | make migrate
```

The Jekyll layer is gone: `_layouts/`, `_config.yml`, `_index.html` and
`_posts/`. All 16 of those posts are in `content/`, verified body for body,
so nothing was lost with the directory.

Their URLs did change, though. Jekyll served them at
`/post/<yyyy>/<mm>/<dd>/<Title>.html` (and `/translation/...` for the two
translated ones); they are now `/words/<slug>.html`.

`redirects.json` maps every one of those 16 old paths to its new page, and
`build.py` writes a canonical + meta-refresh stub at each. GitHub Pages has
no server-side redirects, so a stub file is the only option. Add a row to
`redirects.json` whenever a URL moves; the build fails if a row points at a
page that does not exist.

## Add a piece of writing

Drop a markdown file into `content/`. Front matter:

```markdown
---
title: My Post Title
date: 2026-06-21
kind: essay            # essay | talk | translation | print
tags: data, career     # from the closed TAGS list in build.py
external:              # optional — if set, the item links out and no page is built
summary:               # optional
---

Body in **markdown**...
```

- Notion exports work directly: drop the `.md` in `content/` (the build
  slugifies the filename and strips Notion's hash suffixes).
- `kind` becomes the type badge in the list; `tags` become the clickable
  `#topic` filters. Both filter the single chronological list in place —
  no extra pages or nav.
- `kind` and `tags` are both closed vocabularies (`KINDS` and `TAGS` in
  `build.py`). An unknown value fails the build rather than silently adding
  a permanent dropdown row for a typo.
- `external:` is for talks, podcasts, print pieces, etc. that live
  elsewhere — they appear in the list but link out instead of generating
  a page.

## Add an app to the lab

Edit `lab.json`:

```json
{
  "name": "My App",
  "blurb": "One line about it.",
  "url": "/myapp/",          // in-repo subfolder, or a full external URL
  "external": false,          // true = hosted elsewhere
  "tech": ["python", "react"]
}
```

Self-hosted apps live in a repo subfolder (served at `soobrosa.info/myapp/`);
external ones just link out.

## Develop locally

```bash
make serve        # installs markdown, builds, serves at http://localhost:8000
# or
make build        # just regenerate words.html + words/
python3 -m http.server 8000
```

## Deploy

Push to `master`. The GitHub Action (`.github/workflows/build.yml`)
installs `markdown`, runs `build.py`, and deploys the static output to
GitHub Pages.

> One-time setup: in repo **Settings → Pages**, set the source to
> **GitHub Actions** (instead of the legacy "Deploy from a branch").

Custom domain `soobrosa.info` is configured via `CNAME`.
