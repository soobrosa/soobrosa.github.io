# soobrosa.info

Daniel Molnar's personal site. Pure static HTML in an 8-bit pixel theme,
built from markdown by a tiny Python script. No Jekyll.

## Structure

```
index.html              Bio / landing page
mixes.html              DJ mix player (reads mixes.json, streams from R2)
words.html              GENERATED: one chronological list of all writing
words/<slug>.html       GENERATED: one page per markdown post
lab.html                Apps & experiments (reads lab.json)
musings.html            Static link archive (campervan / tinyhouse / houseboat)
elearning.html          Static link archive (e-learning courses)
404.html

content/*.md            SOURCE for writing — drop markdown here
build.py                content/*.md -> words/<slug>.html + words.html
migrate.py              One-time importer (old _posts/ + static/ -> content/)

assets/css/site.css     Single shared stylesheet (the pixel theme)
covers/                 Mix cover art
mixes.json              Mix list (id, title, url, cover)
lab.json                App list (name, blurb, url, external, tech)

.nojekyll               Disables GitHub's default Jekyll build
.github/workflows/      Build + deploy to GitHub Pages on push
Makefile                make build | make serve | make migrate
```

Legacy Jekyll files (`_posts/`, `_layouts/`, `_config.yml`, old map
experiments, etc.) are kept in the repo but no longer used.

## Add a piece of writing

Drop a markdown file into `content/`. Front matter:

```markdown
---
title: My Post Title
date: 2026-06-21
kind: essay            # essay | talk | translation | print | app
tags: data, music      # freeform topical tags (kept small)
external:              # optional — if set, the item links out and no page is built
summary:               # optional
---

Body in **markdown**...
```

- Notion exports work directly: drop the `.md` in `content/` (the build
  slugifies the filename and strips Notion's hash suffixes).
- `kind` becomes the colored type badge in the list; `tags` become the
  clickable `#topic` filters. Both filter the single chronological list
  in place — no extra pages or nav.
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
