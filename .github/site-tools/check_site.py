"""Check the site's files for mistakes before publishing.

Run from the repository root:  python3 .github/site-tools/check_site.py

Needs only Python 3 (no packages, no browser). It reads the files in the
repository and reports anything inconsistent: an article missing from the
archive list, the sitemap or the feed, a broken link (including links to
sections and footnotes within a page), a missing share card or tag, a
stylesheet version out of step, anything loaded from another website, or a
change to the wording of the home page Notice.

Exit code 0 means no problems; 1 means at least one problem was found.
"Notes" are things for the owner to decide (such as wording) and do not fail.
For how pages actually look in a browser, run check_pages.mjs as well.
"""

import glob
import hashlib
import html
import json
import os
import re
import sys
from urllib.parse import urlparse

SITE_HOST = "apklaw.in"
SUBJECTS = {"general-commercial", "corporate-ma", "regulatory"}
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

# Fingerprint of the home page Notice wording. The Notice must not change
# unless the owner explicitly asks; if they do, update this value (the check
# prints the new one).
NOTICE_SHA256 = "80b95dfe74b6cb3a64dffe3095054c71a4e115b6234dcebe616541ec686e5a11"

problems = []
notes = []


def problem(msg):
    problems.append(msg)


def note(msg):
    """Worth the owner's attention, but not an error (usually a wording choice)."""
    notes.append(msg)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def text_of(fragment):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def check_notice():
    s = read("index.html")
    m = re.search(r"<h2>Notice</h2>(.*?)</section>", s, re.S)
    if not m:
        problem("index.html: the Notice section is missing")
        return
    digest = hashlib.sha256(text_of(m.group(1)).encode()).hexdigest()
    if digest != NOTICE_SHA256:
        problem("index.html: the wording of the Notice has changed. It must stay as "
                "it is unless the owner asked for the change; if they did, set "
                f"NOTICE_SHA256 in check_site.py to {digest}")


def check_articles():
    idx = read("articles/index.html")
    entries = re.findall(
        r'<li data-subject="([^"]+)" data-year="(\d+)">\s*<a href="([^"]+)">\s*'
        r'<span class="art-title">(.*?)</span>\s*<span class="art-year">(\d+)</span>',
        idx, re.S)
    files = sorted(os.path.basename(p) for p in glob.glob("articles/*.html")
                   if not p.endswith("index.html"))
    listed = [e[2] for e in entries]

    for f in files:
        if f not in listed:
            problem(f"articles/{f}: not in the archive list (articles/index.html)")
    for f in listed:
        if f not in files:
            problem(f"articles/index.html: lists {f}, which does not exist")
    for f in set(listed):
        if listed.count(f) > 1:
            problem(f"articles/index.html: lists {f} more than once")

    feed = read("feed.xml") if os.path.exists("feed.xml") else ""
    feed_links = re.findall(r"<link>([^<]+)</link>", feed)
    for f in files:
        if f"https://{SITE_HOST}/articles/{f}" not in feed_links:
            problem(f"articles/{f}: not in feed.xml (the automatic job adds it on main)")

    sitemap = read("sitemap.xml") if os.path.exists("sitemap.xml") else ""
    locs = set(re.findall(r"<loc>([^<]+)</loc>", sitemap))
    for f in files:
        if f"https://{SITE_HOST}/articles/{f}" not in locs:
            problem(f"articles/{f}: not in sitemap.xml (the automatic job adds it on main)")

    version = re.search(r"styles\.css\?v=(\d+)", read("index.html"))
    version = version.group(1) if version else None

    dates = []
    for subject, year, f, list_title, list_year in entries:
        if f not in files:
            continue
        path = f"articles/{f}"
        s = read(path)
        if subject not in SUBJECTS:
            problem(f"articles/index.html: {f} has unknown subject '{subject}'")

        h1 = re.search(r'<h1 class="article-title">(.*?)</h1>', s, re.S)
        date = re.search(r'class="article-date">\s*(\w+)\s+(\d{4})', s)
        if not h1:
            problem(f"{path}: no <h1 class=\"article-title\">")
            continue
        if not date or date.group(1) not in MONTHS:
            problem(f"{path}: no <div class=\"article-date\">Month YYYY</div>")
            continue
        title = text_of(h1.group(1))
        if text_of(list_title) != title:
            problem(f"{path}: title differs from the archive list "
                    f"('{title}' vs '{text_of(list_title)}')")
        if not (year == list_year == date.group(2)):
            problem(f"{path}: year differs between the page ({date.group(2)}) and the "
                    f"archive list (data-year {year}, shown {list_year})")
        dates.append((int(date.group(2)), MONTHS[date.group(1)], f))

        if '<main class="article-body">' not in s or "</main>" not in s:
            problem(f"{path}: missing <main class=\"article-body\">")
        elif "article-disclaimer" not in s:
            problem(f"{path}: missing the disclaimer")
        elif s.index("article-disclaimer") > s.index("</main>"):
            problem(f"{path}: the disclaimer is outside <main>")

        if version and f"styles.css?v={version}" not in s:
            problem(f"{path}: stylesheet version differs from index.html (v={version}); "
                    "the automatic job fixes this on main")

        # Added by the automatic job on main; flagged so a preview is complete.
        for key, what in [('name="description"', "description"),
                          ('property="og:image"', "share image tag"),
                          ('rel="canonical"', "canonical link"),
                          ("application/ld+json", "structured data"),
                          ("/js/article-nav.js", "Earlier/Later links script"),
                          ("application/rss+xml", "feed link")]:
            if key not in s:
                problem(f"{path}: missing {what} (run update_site.py, or the automatic "
                        "job adds it on main)")
        og = re.search(r'property="og:url" content="([^"]+)"', s)
        if og and og.group(1) != f"https://{SITE_HOST}/articles/{f}":
            problem(f"{path}: og:url points to {og.group(1)}")
        og_title = re.search(r'property="og:title" content="([^"]+)"', s)
        if og_title and html.unescape(og_title.group(1)) != title:
            note(f"{path}: the link-preview title ('{html.unescape(og_title.group(1))}') "
                 f"differs from the page title. This is a wording choice for the owner.")
        if not os.path.exists(f"assets/share/{f[:-5]}.jpg"):
            problem(f"{path}: no share card assets/share/{f[:-5]}.jpg")
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                json.loads(block)
            except ValueError as e:
                problem(f"{path}: structured data is not valid JSON ({e})")

    if [d[:2] for d in dates] != sorted((d[:2] for d in dates), reverse=True):
        problem("articles/index.html: the list is not in newest-first order")


def check_links():
    pages = sorted(glob.glob("*.html") + glob.glob("articles/*.html"))
    for page in pages:
        s = read(page)
        for ref in re.findall(r'(?:href|src)="([^"#]*)', s):
            if not ref:
                continue
            u = urlparse(ref)
            if u.scheme in ("http", "https"):
                if u.netloc != SITE_HOST:
                    problem(f"{page}: loads or links to another website ({u.netloc}); "
                            "the site must contact no third party")
                continue
            if u.scheme == "mailto":
                continue
            if u.path.startswith("/"):
                target = u.path.lstrip("/")
            else:
                target = os.path.normpath(os.path.join(os.path.dirname(page), u.path))
            if target == "" or target.endswith("/"):
                target = os.path.join(target, "index.html")
            if not os.path.exists(target):
                problem(f"{page}: broken link or missing file '{ref}'")
        ids = re.findall(r'\bid="([^"]+)"', s)
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            problem(f"{page}: the id '{dup}' is used more than once")
        for frag in re.findall(r'href="#([^"]+)"', s):
            if frag not in ids:
                problem(f"{page}: link to '#{frag}' has no matching section or note")
        if re.search(r"fonts\.(googleapis|gstatic)\.com", s):
            problem(f"{page}: uses Google Fonts; fonts must be served from assets/fonts/")

    css = read("css/styles.css")
    for ref in re.findall(r'url\("?([^")]+)"?\)', css):
        if ref.startswith("data:"):
            continue
        if not os.path.exists(os.path.normpath(os.path.join("css", ref))):
            problem(f"css/styles.css: missing file '{ref}'")
    if re.search(r"@import|https?://", css):
        problem("css/styles.css: refers to another website")


def check_footer():
    from datetime import datetime, timedelta, timezone
    current = datetime.now(timezone(timedelta(hours=5, minutes=30))).year
    years = {}
    for page in sorted(glob.glob("*.html") + glob.glob("articles/*.html")):
        m = re.search(r"<footer>(.*?)</footer>", read(page), re.S)
        text = text_of(m.group(1)) if m else ""
        y = re.fullmatch(r"© (\d{4}) APK Law, Advocates", text)
        if not y:
            problem(f"{page}: footer should read '© YEAR APK Law, Advocates' (found '{text}')")
        else:
            years.setdefault(y.group(1), []).append(page)
    if len(years) > 1:
        problem("footers show different years: " + ", ".join(f"{y} ({len(p)} pages)" for y, p in years.items()))
    elif years and str(current) not in years:
        note(f"the footer year is {next(iter(years))}; the automatic jobs update it to {current}")


def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(root)
    check_notice()
    check_articles()
    check_links()
    check_footer()
    if notes:
        print(f"{len(notes)} note(s) for the owner (not errors):")
        for n_ in notes:
            print(" -", n_)
    if problems:
        print(f"{len(problems)} problem(s) found:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    n = len([p for p in glob.glob("articles/*.html") if not p.endswith("index.html")])
    print(f"No problems found ({n} articles, home page, archive and 404 page checked).")


if __name__ == "__main__":
    main()
