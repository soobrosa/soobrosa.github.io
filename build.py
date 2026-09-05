#!/usr/bin/env python3
"""Static build: content/*.md -> /words/<slug>.html + /index.html (the stream)

Front matter (YAML-ish) per markdown file:
    ---
    title: Some Title
    date: 2016-09-06
    kind: essay            # essay | translation | print
    tags: data, hardware
    external: https://...  # optional; if set, item links out and no page is generated
    summary: one line       # optional
    ---
    markdown body...
"""
import re
import sys
import html
import json
import shutil
import pathlib
import datetime
import unicodedata

try:
    import markdown as md_lib
except ImportError:
    sys.exit("Missing dependency: pip install markdown")

ROOT = pathlib.Path(__file__).parent
CONTENT = ROOT / "content"
WORDS_DIR = ROOT / "words"

# Talks live on media.html, not in the stream, so "talk" is not a kind here.
KINDS = ["essay", "translation", "print"]
# The TOPIC filter is built from whatever tags appear in front matter, so a typo
# or a one-off word silently becomes a permanent dropdown row. Keep this closed.
TAGS = ["career", "culture", "data", "hardware", "learning"]
SITE = "https://soobrosa.info"
CSS = "/assets/css/site.css"
# Every hand-written page loads this; generated pages have to as well or the
# T-key light theme silently stops working on articles only.
THEME_JS = "/assets/js/theme.js"

NAV_ITEMS = [("words", "/index.html"), ("lab", "/lab.html"),
             ("media", "/media.html"), ("mixes", "/mixes.html"),
             ("about", "/about.html")]


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def slugify(s):
    s = strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s) or "post"


def parse_front_matter(text):
    meta, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip()
            body = text[end + 4:].lstrip("\n")
            for line in block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
    return meta, body


def parse_date(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def nav_html(active):
    out = ['<a class="brand" href="/index.html">soobrosa</a>']
    for label, href in NAV_ITEMS:
        cls = ' class="active"' if label == active else ""
        out.append(f'<a href="{href}"{cls}>{label.upper()}</a>')
    return '<nav class="topnav">' + "".join(out) + "</nav>"


FOOTER = ('<footer class="foot">DANIEL MOLNAR &middot; soobrosa@gmail.com &middot; '
          '<a href="https://github.com/soobrosa">github</a></footer>')


def page(title, body, active, narrow=False, extra_head=""):
    wrap = "wrap narrow" if narrow else "wrap"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{CSS}">
<script src="{THEME_JS}"></script>{extra_head}
</head>
<body>
<main class="{wrap}">
{nav_html(active)}
{body}
{FOOTER}
</main>
</body>
</html>
"""


def load_entries():
    entries = []
    if not CONTENT.exists():
        return entries
    for path in sorted(CONTENT.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        title = meta.get("title") or path.stem
        kind = meta.get("kind", "essay").strip().lower()
        if kind not in KINDS:
            sys.exit(f"{path.name}: unknown kind '{kind}'. "
                     f"Add to KINDS in build.py or fix the front matter.")
        tags = [t.strip().lower() for t in meta.get("tags", "").split(",") if t.strip()]
        unknown = [t for t in tags if t not in TAGS]
        if unknown:
            sys.exit(f"{path.name}: unknown tag(s) {', '.join(unknown)}. "
                     f"Add to TAGS in build.py or fix the front matter.")
        date = parse_date(meta.get("date"))
        external = meta.get("external", "").strip()
        slug = slugify(meta.get("slug") or path.stem)
        entries.append({
            "slug": slug, "title": title, "kind": kind, "tags": tags,
            "date": date, "external": external, "body": body,
            "summary": meta.get("summary", ""),
        })
    entries.sort(key=lambda e: (e["date"] or datetime.date.min), reverse=True)
    return entries


def render_article(entry):
    body_html = md_lib.markdown(entry["body"], extensions=["fenced_code", "tables", "sane_lists"])
    d = entry["date"]
    meta = f'&gt; {d.strftime("%-d %b %Y").upper()} :: soobrosa' if d else "soobrosa"
    inner = f"""<a class="back" href="/index.html">&lt;&lt; ALL WORDS</a>
<article class="post">
<h1>{html.escape(entry["title"])}</h1>
<div class="meta">{meta}</div>
{body_html}
</article>"""
    return page(entry["title"] + " // soobrosa", inner, "words", narrow=True)


def render_words(entries):
    rows = []
    prev_year = None
    for e in entries:
        href = e["external"] or f'/words/{e["slug"]}.html'
        ext = ' target="_blank" rel="noopener"' if e["external"] else ""
        year = e["date"].year if e["date"] else None
        # The list is newest-first, so the year label lands on the latest
        # entry of its year and the rest of the group leaves the cell empty.
        label = "&mdash;" if year is None else (str(year) if year != prev_year else "")
        prev_year = year
        rows.append(
            f'<li><span class="date">{label}</span>'
            f'<span class="main"><a class="title-link" href="{href}"{ext}>{html.escape(e["title"])}</a>'
            f'</span></li>')

    body = f"""<h1 class="title">WORDS</h1>
<ul class="words">
{chr(10).join(rows)}
</ul>"""
    # The stream is the homepage, so the title tag is the bare site name.
    return page("soobrosa", body, "words")


REDIRECT_STUB = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Moved &mdash; soobrosa</title>
<link rel="canonical" href="{site}{new}">
<meta http-equiv="refresh" content="0; url={new}">
<link rel="stylesheet" href="{css}">
</head>
<body>
<main class="wrap narrow">
  <div class="panel"><p>This page moved to <a class="inline" href="{new}">{new}</a>.</p></div>
</main>
</body>
</html>
"""


def write_redirects():
    """Emit a stub at every URL the Jekyll site used to serve.

    Jekyll published posts at /<category>/<yyyy>/<mm>/<dd>/<Title>.html. Those
    paths are all still live and indexed, and deleting _posts/ would turn every
    one of them into a 404, so each gets a canonical + meta-refresh stub.

    Nothing is deleted first: these paths are historical facts that only ever
    get added to, and rmtree-ing top-level directories by name is too blunt a
    tool to point at a site root.
    """
    mapping = json.loads((ROOT / "redirects.json").read_text(encoding="utf-8"))
    for old, new in sorted(mapping.items()):
        target = ROOT / old.lstrip("/")
        if not (ROOT / new.lstrip("/")).exists():
            sys.exit(f"redirects.json: {old} points at {new}, which does not exist")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            REDIRECT_STUB.format(site=SITE, new=new, css=CSS), encoding="utf-8")
    return len(mapping)


def render_feed(entries):
    """Atom feed for the whole stream, newest first.

    <updated> is the newest entry date rather than the build time, so that
    rebuilding without content changes leaves the file byte-identical.
    """
    dated = [e for e in entries if e["date"]][:25]
    stamp = lambda d: d.strftime("%Y-%m-%dT00:00:00+00:00")
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<feed xmlns="http://www.w3.org/2005/Atom">',
           " <title>soobrosa aka Daniel Molnar</title>",
           f' <link href="{SITE}/atom.xml" rel="self"/>',
           f' <link href="{SITE}/"/>',
           f" <updated>{stamp(dated[0]['date'])}</updated>",
           f" <id>{SITE}/</id>",
           " <author>",
           "   <name>Daniel Molnar</name>",
           "   <email>soobrosa@gmail.com</email>",
           " </author>"]
    for e in dated:
        link = e["external"] or f'{SITE}/words/{e["slug"]}.html'
        out += [" <entry>",
                f'   <title>{html.escape(e["title"])}</title>',
                f'   <link href="{html.escape(link)}"/>',
                f"   <updated>{stamp(e['date'])}</updated>",
                f'   <id>{html.escape(link)}</id>',
                f'   <category term="{e["kind"]}"/>']
        if e["summary"]:
            out.append(f'   <summary>{html.escape(e["summary"])}</summary>')
        if not e["external"]:
            body = md_lib.markdown(e["body"],
                                   extensions=["fenced_code", "tables", "sane_lists"])
            out.append(f'   <content type="html">{html.escape(body)}</content>')
        out.append(" </entry>")
    out += ["</feed>", ""]
    return "\n".join(out)


def main():
    entries = load_entries()
    if WORDS_DIR.exists():
        shutil.rmtree(WORDS_DIR)
    WORDS_DIR.mkdir(parents=True, exist_ok=True)
    generated = 0
    for e in entries:
        if e["external"]:
            continue
        (WORDS_DIR / f'{e["slug"]}.html').write_text(render_article(e), encoding="utf-8")
        generated += 1
    (ROOT / "index.html").write_text(render_words(entries), encoding="utf-8")
    (ROOT / "atom.xml").write_text(render_feed(entries), encoding="utf-8")
    redirects = write_redirects()
    print(f"built index.html with {len(entries)} entries, {generated} article pages")
    print(f"wrote atom.xml and {redirects} redirect stubs")


if __name__ == "__main__":
    main()
