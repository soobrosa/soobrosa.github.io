#!/usr/bin/env python3
"""Static build: content/*.md -> /words/<slug>.html + /words.html

Front matter (YAML-ish) per markdown file:
    ---
    title: Some Title
    date: 2016-09-06
    kind: essay            # essay | talk | translation | print | app
    tags: data, hardware
    external: https://...  # optional; if set, item links out and no page is generated
    summary: one line       # optional
    ---
    markdown body...
"""
import re
import sys
import html
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

KINDS = ["essay", "talk", "translation", "print", "app"]
CSS = "/assets/css/site.css"

NAV_ITEMS = [("bio", "/index.html"), ("mixes", "/mixes.html"),
             ("words", "/words.html"), ("lab", "/lab.html")]


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
<link rel="stylesheet" href="{CSS}">{extra_head}
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
            kind = "essay"
        tags = [t.strip().lower() for t in meta.get("tags", "").split(",") if t.strip()]
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
    inner = f"""<a class="back" href="/words.html">&lt;&lt; ALL WORDS</a>
<article class="post">
<h1>{html.escape(entry["title"])}</h1>
<div class="meta">{meta}</div>
{body_html}
</article>"""
    return page(entry["title"] + " // soobrosa", inner, "words", narrow=True)


def render_words(entries):
    rows = []
    kinds_present, tags_present = [], []
    for e in entries:
        if e["kind"] not in kinds_present:
            kinds_present.append(e["kind"])
        for t in e["tags"]:
            if t not in tags_present:
                tags_present.append(t)
        href = e["external"] or f'/words/{e["slug"]}.html'
        ext = ' target="_blank" rel="noopener"' if e["external"] else ""
        year = e["date"].year if e["date"] else "&mdash;"
        chips = "".join(
            f'<span class="tag" data-filter="tag:{t}">{t}</span>' for t in e["tags"])
        rows.append(
            f'<li data-kind="{e["kind"]}" data-tags="{",".join(e["tags"])}" '
            f'data-date="{e["date"] or ""}"><span class="date">{year}</span>'
            f'<span class="badge {e["kind"]}" data-filter="kind:{e["kind"]}">{e["kind"][:6].upper()}</span>'
            f'<span class="main"><a class="title-link" href="{href}"{ext}>{html.escape(e["title"])}</a>'
            f'<span class="tags">{chips}</span></span></li>')

    kind_btns = "".join(
        f'<button class="fbtn" data-filter="kind:{k}">{k.upper()}</button>'
        for k in KINDS if k in kinds_present)
    tag_btns = "".join(
        f'<button class="fbtn" data-filter="tag:{t}">{t.upper()}</button>'
        for t in sorted(tags_present))

    body = f"""<h1 class="title">WORDS</h1>
<p class="hint">One chronological stream. Click a <b>TYPE</b> or a <b>#tag</b> to filter in place.</p>
<div class="filters" id="filters">
  <button class="fbtn active" data-filter="all">ALL</button>
  <span class="grp-label">&gt; TYPE</span>{kind_btns}
  <span class="grp-label">&gt; TOPIC</span>{tag_btns}
</div>
<div class="count" id="count"></div>
<ul class="words" id="list">
{chr(10).join(rows)}
</ul>
<div class="empty" id="empty">! NO ENTRIES !</div>
{FILTER_JS}"""
    return page("WORDS // soobrosa", body, "words")


FILTER_JS = """<script>
const list=document.getElementById('list');
const items=[...list.querySelectorAll('li')];
const buttons=[...document.querySelectorAll('.fbtn')];
const countEl=document.getElementById('count');
const emptyEl=document.getElementById('empty');
function apply(f){let shown=0;items.forEach(li=>{let m=f==='all';if(!m){const[t,v]=f.split(':');if(t==='kind')m=li.dataset.kind===v;else if(t==='tag')m=li.dataset.tags.split(',').includes(v);}li.classList.toggle('hidden',!m);if(m)shown++;});
buttons.forEach(b=>b.classList.toggle('active',b.dataset.filter===f));
countEl.textContent=f==='all'?shown+' ENTRIES':shown+'/'+items.length+' \\u00b7 ';
if(f!=='all'){const r=document.createElement('a');r.href='#';r.textContent='CLEAR';r.onclick=e=>{e.preventDefault();go('all');};countEl.appendChild(r);}
emptyEl.style.display=shown?'none':'block';}
function go(f){location.hash=f==='all'?'':f;apply(f);}
document.addEventListener('click',e=>{const t=e.target.closest('[data-filter]');if(!t)return;e.preventDefault();go(t.dataset.filter);});
apply(location.hash.slice(1)||'all');
</script>"""


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
    (ROOT / "words.html").write_text(render_words(entries), encoding="utf-8")
    print(f"built words.html with {len(entries)} entries, {generated} article pages")


if __name__ == "__main__":
    main()
