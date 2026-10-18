# Site tools

Tools for maintaining apklaw.in. None of this is published on the website.

| File | What it does | Needs |
|---|---|---|
| `update_site.py` | Makes share cards, adds missing search and sharing tags, rebuilds `sitemap.xml`. Runs automatically on GitHub after each change to an article. | Python 3, Pillow |
| `check_site.py` | Checks the files: archive list, sitemap, links, tags, share cards, stylesheet version, no third-party sites, Notice wording unchanged. | Python 3 |
| `check_pages.js` | Checks the pages in a real browser at laptop and phone size, and that the home page fits the window. Can save preview screenshots. | Node.js, Playwright |

## Before publishing any change

From the repository root:

```
python3 .github/site-tools/check_site.py
node .github/site-tools/check_pages.js
```

Both must end with "No problems found". To save preview screenshots of the
home page and a particular page:

```
node .github/site-tools/check_pages.js --shots preview --page /articles/<file-name>.html
```

(`preview/` is ignored by git.)

## One-time setup on a new computer

1. Install **Git**, **Python 3** and **Node.js** (version 18 or later).
2. Get the site: `git clone https://github.com/anprku/firm-website.git`
3. From the repository root:

   ```
   pip install pillow
   cd .github/site-tools
   npm install
   npx playwright install chromium
   cd ../..
   ```

Claude Code cloud sessions already have Python, Node and Chromium. If
Playwright is missing there, run the `npm install` step above.
