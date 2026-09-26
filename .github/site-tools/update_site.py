"""Fill in the search and sharing details for articles, and rebuild the sitemap.

Run from the repository root:  python3 .github/site-tools/update_site.py

For every page in articles/ (other than index.html) it:
  - makes a share card at assets/share/<file name>.jpg if there isn't one
    (delete a card to have it made again, e.g. after changing a title);
  - adds any missing tags: description, Open Graph, share image, canonical
    link and schema.org Article data.
Tags already present are left exactly as they are. It also removes any
Google Fonts link (the fonts are served from this site) and points the
stylesheet link at the version the home page uses. It then rewrites
sitemap.xml from the home page, the archive and every article.

An article needs only its title in <h1 class="article-title"> and its date
("Month YYYY") in <div class="article-date">.
"""

import glob
import html
import json
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

SITE = "https://apklaw.in"
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


# ---------- Share cards ----------

W, H = 1200, 630
INK = (43, 43, 43)
GOLD = (200, 164, 107)
MUTED = (110, 104, 96)
PAPER = (244, 242, 236)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def paper():
    bg = Image.new("RGB", (W, H), PAPER)
    grain = Image.open("assets/paper-grain.jpg").convert("RGB")
    scale = W * 1.05 / grain.width
    grain = grain.resize((int(grain.width * scale), int(grain.height * scale)))
    for y in range(0, H, grain.height):
        bg.paste(grain, (0, y))
    return bg


def gold_rule(d, cx, y, w=90):
    for i in range(w):
        t = 1 - abs(i - w / 2) / (w / 2)
        c = tuple(int(PAPER[k] + (GOLD[k] - PAPER[k]) * t) for k in range(3))
        d.line([(cx - w // 2 + i, y), (cx - w // 2 + i, y + 1)], fill=c)


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def make_card(title, subtitle, out):
    """Logo, firm name, gold rule, title and subtitle as one centred block."""
    im = paper()
    d = ImageDraw.Draw(im)

    logo = Image.open("assets/logo.png").convert("RGBA")
    logo = logo.crop(logo.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox())
    lw = 82
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)

    f_name = font("PlayfairDisplay-Bold.ttf", 28)
    f_sub = font("EBGaramond-Regular.ttf", 26)
    size = 50
    while True:
        f_title = font("PlayfairDisplay-Regular.ttf", size)
        lines = wrap(d, title, f_title, W - 220)
        if len(lines) <= 3 or size <= 36:
            break
        size -= 4
    line_h = int(size * 1.3)

    def box(f):
        return d.textbbox((0, 0), "Hg", font=f, anchor="ls")

    def height(f):
        b = box(f)
        return b[3] - b[1]

    gap_logo, gap_rule, gap_title, gap_sub = 38, 18, 44, 40
    name_h = height(f_name)
    title_h = line_h * (len(lines) - 1) + height(f_title)
    sub_h = height(f_sub)
    total = (logo.height + gap_logo + name_h + gap_rule + 1 + gap_title
             + title_h + gap_sub + sub_h)
    y = (H - total) // 2

    im.paste(logo, ((W - lw) // 2, y), logo)
    y += logo.height + gap_logo

    name, spacing = "APK Law, Advocates", 3
    width = sum(d.textlength(c, font=f_name) for c in name) + spacing * (len(name) - 1)
    x = (W - width) / 2
    for c in name:
        d.text((x, y - box(f_name)[1]), c, font=f_name, fill=INK, anchor="ls")
        x += d.textlength(c, font=f_name) + spacing
    y += name_h + gap_rule

    gold_rule(d, W // 2, y)
    y += 1 + gap_title

    for i, line in enumerate(lines):
        d.text((W / 2, y - box(f_title)[1] + i * line_h), line,
               font=f_title, fill=INK, anchor="ms")
    y += title_h + gap_sub

    d.text((W / 2, y - box(f_sub)[1]), subtitle, font=f_sub, fill=MUTED, anchor="ms")
    im.save(out, quality=84, optimize=True, progressive=True)


# ---------- Article tags ----------

def attr(value):
    return html.escape(value, quote=True)


def first_paragraph(s):
    m = re.search(r'<main class="article-body">.*?<p>(.*?)</p>', s, re.S)
    if not m:
        return ""
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).split())
    return text if len(text) <= 200 else text[:197].rsplit(" ", 1)[0] + "…"


def meta(s, attr_name, key):
    m = re.search(r'<meta %s="%s" content="([^"]*)">' % (attr_name, re.escape(key)), s)
    return html.unescape(m.group(1)) if m else None


def update_article(path):
    s = original = open(path, encoding="utf-8").read()
    file_name = os.path.basename(path)
    slug = file_name[:-5]
    url = f"{SITE}/articles/{file_name}"
    image = f"{SITE}/assets/share/{slug}.jpg"

    m = re.search(r'<h1 class="article-title">(.*?)</h1>', s, re.S)
    d = re.search(r'class="article-date">\s*(\w+)\s+(\d{4})', s)
    if not m or not d or d.group(1) not in MONTHS:
        print(f"skipped {path}: needs <h1 class=\"article-title\"> and "
              f"<div class=\"article-date\">Month YYYY</div>")
        return False
    title = " ".join(html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).split())
    month_year = f"{d.group(1)} {d.group(2)}"
    published = f"{d.group(2)}-{MONTHS[d.group(1)]:02d}"

    card = f"assets/share/{slug}.jpg"
    if not os.path.exists(card):
        os.makedirs("assets/share", exist_ok=True)
        make_card(title, "Notes and Reflections  ·  " + month_year, card)
        print(f"made {card}")

    description = (meta(s, "name", "description")
                   or meta(s, "property", "og:description")
                   or first_paragraph(s))

    wanted = [
        ('name="description"', f'<meta name="description" content="{attr(description)}">'),
        ('property="og:type"', '<meta property="og:type" content="article">'),
        ('property="og:title"', f'<meta property="og:title" content="{attr(title)}">'),
        ('property="og:description"', f'<meta property="og:description" content="{attr(description)}">'),
        ('property="og:url"', f'<meta property="og:url" content="{url}">'),
        ('property="og:site_name"', '<meta property="og:site_name" content="APK Law">'),
        ('property="og:image"', f'<meta property="og:image" content="{image}">'),
        ('property="og:image:width"', '<meta property="og:image:width" content="1200">'),
        ('property="og:image:height"', '<meta property="og:image:height" content="630">'),
        ('property="og:image:alt"', f'<meta property="og:image:alt" content="{attr(title)}">'),
        ('name="twitter:card"', '<meta name="twitter:card" content="summary_large_image">'),
        ('property="article:published_time"', f'<meta property="article:published_time" content="{published}">'),
        ('rel="canonical"', f'<link rel="canonical" href="{url}">'),
    ]
    missing = [tag for key, tag in wanted if key not in s]

    if 'application/ld+json' not in s:
        data = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "datePublished": published,
            "inLanguage": "en-IN",
            "url": url,
            "mainEntityOfPage": url,
            "image": image,
            "author": {"@type": "Organization", "name": "APK Law, Advocates", "url": SITE + "/"},
            "publisher": {"@type": "Organization", "name": "APK Law, Advocates", "url": SITE + "/",
                          "logo": {"@type": "ImageObject",
                                   "url": SITE + "/assets/android-chrome-512x512.png"}},
        }
        missing.append('<script type="application/ld+json">\n'
                       + json.dumps(data, ensure_ascii=False, indent=2) + '\n</script>')

    if missing:
        block = "\n".join(missing) + "\n\n"
        # Keep the tags together, ahead of the favicons, as on the other articles.
        at = s.find('<link rel="icon"')
        if at < 0:
            at = s.find("</head>")
        s = s[:at] + block + s[at:]

    # Fonts are served from this site; drop any Google Fonts link pasted in.
    s = re.sub(r'\n?<link[^>]*fonts\.(googleapis|gstatic)\.com[^>]*>\n', "\n", s)

    # Point at the current stylesheet version, as used by the home page.
    version = re.search(r'styles\.css(\?v=\d+)?"', open("index.html", encoding="utf-8").read())
    if version:
        s = re.sub(r'(href="/?(?:\.\./)?css/styles\.css)(\?v=\d+)?"',
                   lambda m: 'href="/css/styles.css' + (version.group(1) or "") + '"', s)

    if "/js/article-nav.js" not in s and "</body>" in s:
        s = s.replace("</body>", '<script src="/js/article-nav.js" defer></script>\n\n</body>', 1)

    if s != original:
        open(path, "w", encoding="utf-8").write(s)
        print(f"updated {path}")
        return True
    return False


# ---------- Sitemap ----------

def last_changed(path):
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", path],
                         capture_output=True, text=True).stdout.strip()
    return out or None


def write_sitemap(articles):
    pages = [(f"{SITE}/", "index.html"), (f"{SITE}/articles/", "articles/index.html")]
    pages += [(f"{SITE}/{p}", p) for p in articles]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, path in pages:
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        changed = last_changed(path)
        if changed:
            lines.append(f"    <lastmod>{changed}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>\n")
    text = "\n".join(lines)
    old = open("sitemap.xml", encoding="utf-8").read() if os.path.exists("sitemap.xml") else ""
    if text != old:
        open("sitemap.xml", "w", encoding="utf-8").write(text)
        print("updated sitemap.xml")


if __name__ == "__main__":
    articles = sorted(p for p in glob.glob("articles/*.html")
                      if os.path.basename(p) != "index.html")
    for p in articles:
        update_article(p)
    write_sitemap(articles)
