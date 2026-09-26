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
- **Changes go through a pull request** from the working branch into `main`.
  Merge only when the owner says so.

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
Bengaluru, India | © APK 2026
</footer>

</body>
</html>
```

Formatting conventions, as used in the existing articles:

- **Headings:** `<h2>`, numbered with Roman numerals as the author writes them
  ("I. Introduction", "II. …").
- **Paragraphs:** each in its own `<p>`.
- **Case names** in italics: `<em>Vidya Drolia v. Durga Trading Corporation</em>`.
  Pasted text often loses italics, so italicise case names and list which ones
  you italicised when you report back.
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
- The footer year stays as in the other pages unless the owner says otherwise.

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
description, Open Graph, canonical and schema.org tags and the Earlier/Later
links script, and updates `sitemap.xml`. It only adds what is missing and never
edits the article text.

To let the owner see the finished result before merging, run the script
locally (`pip install pillow`, then `python3 .github/site-tools/update_site.py`
from the repository root) and commit what it produces; the workflow then finds
nothing left to do. The description it adds is the first paragraph, cut to
about 200 characters. If the owner wants a different summary for search results
and link previews, put it in `<meta name="description">` before running the
script.

### Before opening the pull request

- Serve the site locally (`python3 -m http.server`) and check the new article at
  desktop and phone widths: headings, italics, footnotes, tables, the
  disclaimer, and the Earlier/Later links.
- Check the archive list shows the article in the right place and under the
  right subject filter.
- Show the owner the share card image.
- In the pull request and in the chat, list anything you were unsure about
  (italicised case names, suspected typos, heading levels).

After merging, confirm the workflow run succeeded.
