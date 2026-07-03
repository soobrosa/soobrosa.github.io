#!/usr/bin/env python3
"""One-time migration: _posts/ + static/ + old curated link-lists -> content/*.md

Run once locally. After this, content/*.md is the source of truth (same place
Notion exports get dropped) and build.py turns it into the static site.
"""
import re
import pathlib
import unicodedata

ROOT = pathlib.Path(__file__).parent
CONTENT = ROOT / "content"
CONTENT.mkdir(exist_ok=True)

TRANSLATION_HINTS = ("gibson", "alan_kay", "kay", "hakim", "wilson")


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def slugify(s):
    s = strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s) or "post"


def guess_tags(text):
    t = strip_accents(text).lower()
    tags = []
    def add(x):
        if x not in tags:
            tags.append(x)
    if re.search(r"redshift|sql|etl|csv|tableau|mysql|\bdata\b|miso|hubway|metl|dump|sheets|janitor|tensorflow", t):
        add("data")
    if re.search(r"iot|movidius|rpi|raspberry|deep.?learning|edge|sensor|hardware|neural", t):
        add("hardware")
    if re.search(r"present|teach|zoom|keynote|expert|career|shoestring", t):
        add("career")
    if re.search(r"gibson|kay|hakim|wilson|tokyo|matrix|cyberpunk|pornogr|mediamix|xanner|memetik|filozofus|hangero", t):
        add("culture")
    if re.search(r"educa|wiki|edutainment|learning|elearning", t):
        add("learning")
    return tags or ["data"]


def guess_kind(slug, title):
    blob = (slug + " " + title).lower()
    if any(h in blob for h in TRANSLATION_HINTS):
        return "translation"
    return "essay"


def write(slug, title, date, kind, tags, body="", external="", summary=""):
    path = CONTENT / f"{slug}.md"
    if path.exists():
        return False
    fm = ["---", f"title: {title}", f"date: {date}", f"kind: {kind}",
          f"tags: {', '.join(tags)}"]
    if external:
        fm.append(f"external: {external}")
    if summary:
        fm.append(f"summary: {summary}")
    fm.append("---")
    path.write_text("\n".join(fm) + "\n\n" + body.strip() + "\n", encoding="utf-8")
    return True


# ---- 1. _posts/*.md (already markdown w/ Jekyll front matter) ----
date_re = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})-(.+)\.(md|html)$")
gist_re = re.compile(r"\{%\s*gist\s+([0-9a-f]+).*?%\}")


def jekyll_meta(text):
    meta, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
            body = text[end + 4:].lstrip("\n")
    return meta, body


def iso(y, m, d):
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


posts = ROOT / "_posts"
xmp_re = re.compile(r"<xmp[^>]*>(.*?)</xmp>", re.S | re.I)
h1_re = re.compile(r"^#\s+(.+)$", re.M)


def extract_xmp(text):
    m = xmp_re.search(text)
    return m.group(1).strip() if m else text


for p in sorted(posts.glob("*")) if posts.exists() else []:
    m = date_re.match(p.name)
    if not m:
        continue
    y, mo, da, rest, ext = m.groups()
    date = iso(y, mo, da)
    raw = p.read_text(encoding="utf-8", errors="replace")
    if ext == "md":
        meta, body = jekyll_meta(raw)
        title = meta.get("title", rest.replace("_", " ").replace("-", " ")).strip()
        body = gist_re.sub(r"[View the gist](https://gist.github.com/soobrosa/\1)", body)
        kind = "translation" if meta.get("category") == "translation" else guess_kind(rest, title)
    else:  # html w/ xmp
        body = extract_xmp(raw)
        hm = h1_re.search(body)
        title = hm.group(1).strip() if hm else rest.replace("-", " ")
        if hm:
            body = body[:hm.start()] + body[hm.end():]
        kind = guess_kind(rest, title)
    write(slugify(rest), title, date, kind, guess_tags(rest + " " + title + " " + body), body=body)


# ---- 2. static/*.html (strapdown markdown in <xmp>) ----
STATIC_DATES = {
    "1mil": "2016-03-22", "iot": "2016-09-06",
    "User-session-flows-with-redshift": "2015-02-12",
}
static = ROOT / "static"
for p in sorted(static.glob("*.html")) if static.exists() else []:
    raw = p.read_text(encoding="utf-8", errors="replace")
    body = extract_xmp(raw)
    hm = h1_re.search(body)
    title = hm.group(1).strip() if hm else p.stem.replace("-", " ").replace("_", " ")
    if hm:
        body = body[:hm.start()] + body[hm.end():]
    dm = date_re.match(p.name)
    if dm:
        date = iso(dm.group(1), dm.group(2), dm.group(3))
        slug = slugify(dm.group(4))
    else:
        date = STATIC_DATES.get(p.stem, "")
        slug = slugify(p.stem)
    write(slug, title, date, guess_kind(slug, title),
          guess_tags(p.stem + " " + title + " " + body), body=body)


# ---- 3. curated external items (talks / articles / translations / external essays) ----
# (date, title, kind, tags, url)
EXTERNAL = [
    # External essays / blog posts (PDAE + gists)
    ("2022-02-18", "Learn data engineering on a shoestring - Part 2", "essay", ["data", "career"], "https://www.dataengineering.academy/pipeline-data-engineering-academy-blog/learn-data-engineering-on-a-shoestring-free-courses"),
    ("2021-07-26", "How to teach data engineering", "essay", ["data", "career"], "https://www.dataengineering.academy/pipeline-data-engineering-academy-blog/how-to-teach-data-engineering"),
    ("2021-06-29", "Pipeline Academy on the Data Engineering Podcast Vol. 2", "talk", ["data"], "https://www.dataengineering.academy/pipeline-data-engineering-academy-blog/pipeline-academy-on-the-data-engineering-podcast-vol2"),
    ("2020-12-15", "Become a data engineer on a shoestring", "essay", ["data", "career"], "https://www.dataengineering.academy/pipeline-data-engineering-academy-blog/become-a-data-engineer-on-a-shoestring"),
    ("2020-10-03", "Presenting and Teaching via Zoom 101", "essay", ["career"], "https://www.dataengineering.academy/pipeline-data-engineering-academy-blog/presenting-and-teaching-via-zoom-101"),
    ("2020-09-23", "Data Engineering Podcast With The Data Janitor", "talk", ["data"], "https://www.dataengineering.academy/pipeline-data-engineering-academy-blog/data-engineering-podcast-pipeline-academy"),
    ("2020-08-07", "I'm not an expert, I have experience", "essay", ["career"], "https://www.dataengineering.academy/pipeline-data-engineering-academy-blog/data-engineering-data-janitor-keynotes"),
    ("2020-06-21", "Keynotes to remember", "essay", ["career"], "https://www.dataengineering.academy/pipeline-data-engineering-academy-blog/data-engineering-keynotes-to-remember"),
    ("2020-05-17", "Own Your Data - like fo' real.", "essay", ["data"], "https://www.dataengineering.academy/pipeline-data-engineering-academy-blog/own-your-data-like-fo-real"),
    ("2018-04-10", "POSTER: Towards an IoT platform with long-range wireless communication for atmospheric sensing (EGU 2018)", "talk", ["hardware", "data"], "https://meetingorganizer.copernicus.org/EGU2018/EGU2018-12200.pdf"),
    ("2016-02-05", "Own the list of your favourite tracks on Spotify", "essay", ["music", "data"], "https://gist.github.com/soobrosa/a6119b2ee35555c296f3"),
    # Talks & TV
    ("2020-06-01", "What Makes or Breaks a Data Engineer", "talk", ["data", "career"], "https://speakerdeck.com/soobrosa/what-makes-or-breaks-a-data-engineer-96635240-6633-4e30-9ed2-9bbfc547a09d"),
    ("2018-06-01", "The Data Janitor Returns", "talk", ["data"], "https://www.youtube.com/watch?v=LTJNnlBBzuw"),
    ("2017-06-01", "Tensorflow for Janitors", "talk", ["data"], "https://www.youtube.com/watch?v=OSkL7AXu6tY"),
    ("2016-11-01", "Data Janitor 101", "talk", ["data"], "https://www.youtube.com/watch?v=oKWmg3oBJgc"),
    ("2016-06-01", "Migrating a data stack from AWS to Azure (via Raspberry Pi)", "talk", ["data", "hardware"], "https://www.youtube.com/watch?v=QhXPANTd9nE"),
    ("2015-06-01", "Being a Data Janitor for 10m+ Users", "talk", ["data"], "https://speakerdeck.com/soobrosa/being-a-data-janitor-for-10m-plus-users"),
    ("2014-08-01", "Interview: Olvastuk Gibsont, volt Tetsuonk...", "print", ["culture"], "http://www.artmagazin.hu/artmagazin_hirek/olvastuk_gibsont_volt_tetsuonk_ezerrel_ment_az_electronic_body_music_kezdodott_a_rave..2440.html"),
    ("2013-01-01", "Big Data - Over the Hype (Superweek 2013)", "talk", ["data"], "https://speakerdeck.com/soobrosa/big-data-over-the-hype"),
    ("2012-03-01", "Interactive Dashboard: The Blockbuster Meter", "app", ["data"], "https://public.tableau.com/app/profile/balazs.krich/viz/Whatmovieshouldwewatchtonight/Opinionmeter"),
    ("2010-01-01", "Data Bootcamp @ Barcamp Budapest", "talk", ["data"], "http://www.slideshare.net/soobrosa/data-at-barcamp-budapest-hun"),
    ("2007-09-01", "New Ways and Approaches in E-learning", "talk", ["learning"], "http://www.slideshare.net/soobrosa/new-ways-and-approaches"),
    ("2007-03-01", "Virtual Exhibition Space @ Budapest New Technology Meetup", "talk", ["culture"], "https://www.youtube.com/watch?v=FOT4sRaPFwo"),
    ("1995-01-01", "TV Show 'Mediamix' on cyberpunks", "talk", ["culture"], "https://www.youtube.com/watch?v=HHpTeBQ-ruk"),
    ("1994-01-01", "Discmag: XANNER on cyberpunk", "print", ["culture"], "/holder/xanner_no_1.zip"),
    # Print articles
    ("2001-03-01", "Watashi wa baka gaijin desu - Tokyo Underground review", "print", ["culture"], "http://www.iv.hu/modules.php?name=IVlapok&op=viewarticle&artid=668"),
    ("2000-09-01", "Egy filozofus enkeresese a virtualitas tukreben", "print", ["culture"], "http://www.iv.hu/modules.php?name=IVlapok&op=viewarticle&artid=251"),
    ("2000-03-01", "Matrix - valogatas a nettime levelezolista anyagabol", "print", ["culture"], "http://www.iv.hu/modules.php?name=IVlapok&op=viewarticle&artid=347"),
    ("1999-01-01", "Infohaboru, mediamarkec - Ars Electronica", "print", ["culture"], "http://www.filmvilag.hu/xereses_aktcikk_c.php?&cikk_id=3933"),
    ("1998-10-01", "A hangero velunk van - Multihang", "print", ["culture"], "http://www.filmvilag.hu/xereses_aktcikk_c.php?&cikk_id=3818"),
    ("1998-06-01", "Minden szorfos azt akarja - Pornografia az Interneten", "print", ["culture"], "http://www.filmvilag.hu/xereses_aktcikk_c.php?&cikk_id=3720"),
    # Translations
    ("2009-05-01", "Ken Robinson: Do schools kill creativity?", "translation", ["culture", "career"], "https://www.ted.com/talks/ken_robinson_says_schools_kill_creativity/transcript?language=hu"),
    ("2001-03-15", "Hakim Bey: Kaosz - az ontologikus anarchizmus szorolapjain", "translation", ["culture"], "http://www.iv.hu/modules.php?name=IVlapok&op=viewarticle&artid=144"),
    ("1999-03-01", "Michael Wilson: Memetikus tervezes", "translation", ["culture"], "http://www.iv.hu/modules.php?name=IVlapok&op=viewarticle&artid=463"),
]

for date, title, kind, tags, url in EXTERNAL:
    write(slugify(f"{date}-{title}")[:80], title, date, kind, tags, external=url)

print(f"content/ now has {len(list(CONTENT.glob('*.md')))} markdown files")
