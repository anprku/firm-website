# APK Law website (apklaw.in)

A static site for an advocate practising in Bengaluru, served by GitHub Pages
from `main`. The owner is a lawyer, not a developer: explain things in plain
language and avoid jargon.

## Ground rules

- **Restraint.** Bar Council of India rules restrict advertising and
  solicitation by advocates. Do not add marketing language, practice-area
  pages, client names, testimonials, calls to action, analytics, cookies or
  tracking. Leave the Notice on the home page exactly as it is.
- **No third parties.** Fonts are served from `assets/fonts/`. Never add Google
  Fonts, CDNs or external scripts. The Notice tells visitors the site contacts
  no one but the host.
- **The author's words are final.** When turning text into a page, never
  reword, correct, summarise or "improve" the author's writing, citations or
  punctuation. If something looks like a typo, point it out and ask; do not
  change it.
- **Check before every pull request.** Run both checks (see "Checking the
  site" below); both must report "No problems found".
- **Changes go through a pull request** from the working branch into `main`.
  For a **new article**, the owner has agreed that you merge it yourself once
  every check under "Before opening the pull request" passes, then send the
  owner the link, a preview screenshot and the share card. Any other change to
  the site (design, text on existing pages, settings) waits for the owner's
  approval before merging.

## Publishing a new article

The owner will usually paste the article text into the chat. Before building
the page, make sure you have:

1. **Title**
2. **Month and year** to show, e.g. "March 2027"
3. **Subject**: one of General Commercial, Corporate/M&A or Regulatory
4. **The text**, with its headings and any footnotes or tables

Ask for anything missing. Suggest a file name made of short lowercase keywords
joined by hyphens, in the style of the existing ones (e.g.
`arbitral-seat-venue-indian-arbitration-law.html`), and confirm it, because it
becomes the permanent web address.

### The article page: `articles/<file-name>.html`

Use this skeleton. Copy the stylesheet version (`?v=N`) from `index.html`.

```html
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>TITLE</title>

<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png">
<link rel="icon" href="/assets/favicon.ico">

<link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">

<link rel="icon" type="image/png" sizes="192x192" href="/assets/android-chrome-192x192.png">
<link rel="icon" type="image/png" sizes="512x512" href="/assets/android-chrome-512x512.png">

<link rel="stylesheet" href="/css/styles.css?v=N">

</head>

<body>

<header>

<a class="back-link" href="/articles/">← Notes and Reflections</a>

<h1 class="article-title">
TITLE
</h1>

<div class="article-date">MONTH YEAR</div>

</header>


<main class="article-body">

<h2>I. Introduction</h2>

<p>
First paragraph.
</p>

<!-- ... the rest of the article ... -->

<div class="article-disclaimer">
<p>This article is provided for general informational and discussion purposes only and does not constitute legal advice, legal opinion, or a recommendation. It should not be relied upon as a substitute for obtaining professional legal advice in relation to any specific matter. This article has been prepared for publication on the website and other professional platforms and therefore does not follow formal legal citation conventions. The views expressed are personal to the author.</p>
</div>

</main>


<footer>
© 2026 APK Law, Advocates
</footer>

</body>
</html>
```

Formatting conventions, as used in the existing articles:

- **Headings:** `<h2>`, numbered with Roman numerals as the author writes them
  ("I. Introduction", "II. …").
- **Paragraphs:** each in its own `<p>`.
- **No added italics.** Keep the text exactly as pasted; do not italicise case
  names or anything else unless the owner asks. (Some older articles have
  italicised case names; leave those as they are.)
- **Quoted extracts** from statutes or judgments: `<blockquote>`.
- **Footnotes:** a marker in the text, `<sup>1</sup>`, and the notes at the end
  of the article, inside `<main>` and before the disclaimer:

  ```html
  <div class="article-notes">
  <h2>Notes</h2>
  <ol>
  <li>First note.</li>
  </ol>
  </div>
  ```

- **Tables:** a caption, then the table:

  ```html
  <p class="table-caption">Caption</p>
  <table class="article-table">
    <thead><tr><th>Heading</th></tr></thead>
    <tbody><tr><td>Cell</td></tr></tbody>
  </table>
  ```

- Escape `&` as `&amp;` in the text, and `<` and `>` as `&lt;` and `&gt;`.
  Keep the author's quotation marks and dashes as given.
- The footer reads "© YEAR APK Law, Advocates" with the same year as the other
  pages. The automatic jobs keep the year current on every page.

See `articles/director-liability-labour-codes-india.html` for an article with
footnotes and tables.

### The archive entry: `articles/index.html`

Add one entry to the list, which runs newest first by date:

```html
    <li data-subject="SUBJECT" data-year="YEAR">
      <a href="FILE-NAME.html">
        <span class="art-title">TITLE</span>
        <span class="art-year">YEAR</span>
      </a>
    </li>
```

`SUBJECT` is `general-commercial`, `corporate-ma` or `regulatory`.

### Everything else happens automatically

When the change reaches `main`, the GitHub Actions workflow
`.github/workflows/update-site.yml` runs `.github/site-tools/update_site.py`,
which makes the share card (`assets/share/<file-name>.jpg`), adds the
description, Open Graph, canonical, feed and schema.org tags and the
Earlier/Later links script, and updates `sitemap.xml` and the RSS feed
(`feed.xml`). It only adds what is missing and never changes the article's
words.

To let the owner see the finished result before merging, run the script
locally (`pip install pillow`, then `python3 .github/site-tools/update_site.py`
from the repository root) and commit what it produces; the workflow then finds
nothing left to do. The description it adds is the first paragraph, cut to
about 200 characters. If the owner wants a different summary for search results
and link previews, put it in `<meta name="description">` before running the
script.

### Before opening the pull request

- Run both checks (see "Checking the site") and save previews of the new
  article: `node .github/site-tools/check_pages.js --shots preview --page /articles/<file-name>.html`.
  Look at the screenshots yourself: headings, footnotes, tables, the
  disclaimer and the Earlier/Later links.
- Check the archive list shows the article in the right place and under the
  right subject filter.
- Show the owner the share card image.
- In the pull request and in the chat, list anything you were unsure about
  (suspected typos, heading levels).

Then merge (see Ground rules), confirm the workflow run succeeded, and send
the owner the live link, the preview and the share card. If you were unsure
about anything, ask before merging instead.

## Checking the site

Two tools in `.github/site-tools/` (setup and details in its `README.md`):

```
python3 .github/site-tools/check_site.py     # the files: needs only Python
node .github/site-tools/check_pages.js       # real browser: needs Node + Playwright
```

- `check_site.py` checks the archive list, sitemap, links, tags, share cards,
  stylesheet version, that nothing loads from another website, and that the
  Notice wording is unchanged. "Notes" it prints (such as a link-preview title
  that differs from the page title) are wording choices for the owner, not
  errors; mention them, don't change them.
- `check_pages.js` opens every page at laptop and phone size and checks the home
  page fits the window at eight common laptop and monitor sizes. Add
  `--shots preview --page /path.html` to save screenshots for the owner.

A third tool, `python3 .github/site-tools/check_live.py`, checks the live site
at apklaw.in (pages answer over https, certificate, latest version live). It
needs internet access to apklaw.in, which some cloud sessions don't have.

**Monthly self-check:** `.github/workflows/monthly-check.yml` runs all three on
the 1st of each month and keeps the footer year current. If something fails it
opens a GitHub issue labelled `site-check` (GitHub emails the owner) and closes
it once everything passes again. If the owner asks you to look at such an
issue, read it and the linked workflow run, fix the cause, and run the checks.

Run both before every pull request and report what they said. If Playwright is
not installed, follow the README's one-time setup; don't skip the check.

## Design rules (don't undo these)

- **Fonts** are Playfair Display (headings) and EB Garamond (text, with its
  italic), served from `assets/fonts/`. Add no other fonts.
- **Stylesheet version.** Every page links `css/styles.css?v=N`. After any
  change to `css/styles.css`, raise N by one on all pages (home, 404, archive and
  every article), so visitors' browsers fetch the new file. The automatic job
  also brings articles in line with the version used by `index.html`.
- **Earlier/Later links script.** Articles load `js/article-nav.js?v=N`. After
  any change to that file, raise `NAV_VERSION` in `update_site.py` and run it;
  it updates the version on every article. The script reads the archive list
  with `cache: 'no-cache'` so a just-published article finds its neighbours.
- **Shared styles live in `css/styles.css`**, including those for article
  tables (`article-table`, `table-caption`), footnote markers and the Notes
  section (`article-notes`). Don't add `<style>` blocks to individual pages.
- **Paragraphs are justified, without automatic hyphenation**, on every screen
  size, phones included. The owner chose this.
- **Colours for text:** body text `#2b2b2b` and secondary text (back links,
  dates, years, footer, "Bengaluru") `#5c5c5c`, which keep at least 4.5:1
  contrast on the paper, including where it is shaded near the edges. The
  owner chose `#5c5c5c` over the earlier `#666` once the shading was added.
- **The background** is the paper texture (`assets/paper-grain.jpg`), shaded
  very slightly darker towards the edges of the window (`body::before` in
  `css/styles.css`), on every page. The owner chose this over a gold border
  and a faint tree watermark; don't add borders, watermarks, photographs or
  patterns.
- **Pale gold `#c8a46b` is the site's accent**, for the thin rules, borders,
  and the colour links turn on hover. The owner chose it deliberately ("it
  doesn't shine, but it has value"); don't replace it with a deeper gold.
- **Keyboard focus** turns a link or button pale gold, as on hover, with no
  outline box. The owner doesn't want boxes around focused items.
- **The footer** reads "© YEAR APK Law, Advocates" on every page; the
  automatic jobs keep the year current.
- **No section links or clickable footnotes.** Headings and footnote numbers
  stay plain text. The owner tried "§" section links and linked footnotes and
  had them removed as out of keeping with the site; don't add them, or
  anything like them, again.
- **The name block** is the tree logo, "APK Law, Advocates" with its gold
  rule, and "Bengaluru" beneath in ordinary lettering (`.site-place`, grey), as
  on a letterhead. The owner chose ordinary lettering over capitals, and close
  spacing around "Bengaluru". It is the same everywhere the logo and name
  appear together: the home page, the 404 page and every share card (each
  article's card and `assets/share/default.jpg`, all drawn by `make_card` in
  `update_site.py`). Any change to the name block is made in all of these
  places in the same pull request, without the owner having to ask for each.
  After changing `make_card`, raise `CARD_VERSION` in `update_site.py` and run
  it; it makes every card again, the default card included.
- **The home page** (`index.html`, `body class="home"`):
  - Phones and small tablets (under 900px): one column, in the order Notice,
    Notes and Reflections, The Practice.
  - 900px and wider: two columns. The Notice is on the left; Notes and
    Reflections (with "The Writings" button), a thin rule, then The Practice are
    on the right. A faint vertical rule separates them.
  - At 900px and wider, every size on the home page comes from one unit,
    `--fs = clamp(14px, min(1.18vw, 2.3vh), 24px)`: text, headings, button,
    logo, title, header and footer spacing, and the column width
    (`65.5 × --fs`). Because it follows the window's height as well as its
    width, the whole page, footer included, fits the browser window without
    scrolling. Don't replace these with fixed sizes. On short windows (640px
    high or less) the space around the columns is trimmed slightly so the
    page still fits once the text reaches its 14px minimum.
  - The width ratio 65.5 was chosen because ratios from 64.5 to 67 leave no
    justified line with stretched word gaps at any common size. If the home page
    text changes, run `check_pages.js`; if it reports wide gaps or scrolling,
    test other ratios in that range rather than adding hyphens or changing the
    owner's words.
  - The text of the Notice and of The Practice is the owner's. Change it only
    when they ask. `check_site.py` holds a fingerprint of the Notice and fails
    if its wording changes; if the owner does ask, update the fingerprint it
    prints.

## Working from any Claude Code session

The site is plain files on GitHub, and the automatic job runs on GitHub, so it
can be maintained from Claude Code on the owner's computer or in the cloud
alike. Work on a branch, open a pull request into `main` (with the GitHub tools
available in the session, or by pushing the branch and asking the owner to
open it on github.com), and follow the merge rule in Ground rules. After a
merge that touches `articles/`, confirm the "Update search and sharing
details" workflow run on GitHub succeeded.

