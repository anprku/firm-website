/*
Check how the site's pages behave in a real browser before publishing.

Run from the repository root:
  node .github/site-tools/check_pages.js
  node .github/site-tools/check_pages.js --shots preview/ --page /articles/some-article.html

Needs Node.js and Playwright with Chromium (see .github/site-tools/README.md
for the one-time setup). The script serves the site itself; no other server
is needed.

It opens every page at a laptop size and a phone size and reports anything
that fails to load, any request to another website, any script error, any
page wider than the screen, missing fonts or images, and articles without
their Earlier/Later links. It checks that the archive filters add up, and
that the home page fits the browser window without scrolling at common
laptop and monitor sizes.

--shots DIR   also save screenshots (home page, plus any --page) into DIR
--page PATH   a page to screenshot, e.g. /articles/new-article.html (repeatable)

Exit code 0 means no problems; 1 means at least one problem was found.
*/

const fs = require("fs");
const http = require("http");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");

function loadPlaywright() {
  const candidates = ["playwright", path.join(__dirname, "node_modules", "playwright")];
  try {
    const globalRoot = require("child_process").execSync("npm root -g", { stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
    candidates.push(path.join(globalRoot, "playwright"));
  } catch (e) { /* npm not available */ }
  for (const c of candidates) {
    try { return require(c); } catch (e) { /* try next */ }
  }
  console.error("Playwright is not installed. See .github/site-tools/README.md for setup.");
  process.exit(2);
}

async function launch(chromium) {
  try {
    return await chromium.launch();
  } catch (err) {
    // Fall back to a Chromium already on the machine (e.g. a preinstalled one).
    const base = process.env.PLAYWRIGHT_BROWSERS_PATH || "/opt/pw-browsers";
    if (fs.existsSync(base)) {
      for (const dir of fs.readdirSync(base).filter(d => /^chromium-\d+$/.test(d)).sort().reverse()) {
        const exe = path.join(base, dir, "chrome-linux", "chrome");
        if (fs.existsSync(exe)) return chromium.launch({ executablePath: exe });
      }
    }
    throw err;
  }
}

const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
  ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon", ".woff2": "font/woff2",
  ".xml": "application/xml", ".txt": "text/plain",
};

function serve() {
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, "http://x").pathname);
    let file = path.join(ROOT, p);
    if (!file.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, "index.html");
    if (!fs.existsSync(file)) {
      res.writeHead(404, { "Content-Type": TYPES[".html"] });
      return res.end(fs.readFileSync(path.join(ROOT, "404.html")));
    }
    res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
    res.end(fs.readFileSync(file));
  });
  return new Promise(resolve => server.listen(0, "127.0.0.1", () => resolve(server)));
}

// Browser windows (screen size minus toolbars) at which the home page must fit.
const HOME_WINDOWS = [
  [1280, 600, "1280x720 screen"], [1366, 640, "1366x768 laptop"], [1280, 680, "1280x800 laptop"],
  [1536, 730, "1536x864 laptop"], [1440, 780, "1440x900 laptop"], [1680, 920, "1680x1050 monitor"],
  [1920, 950, "1920x1080 monitor"], [2560, 1300, "2560x1440 monitor"],
];

async function main() {
  const args = process.argv.slice(2);
  let shotsDir = null; const shotPages = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--shots") shotsDir = path.resolve(args[++i]);
    else if (args[i] === "--page") shotPages.push(args[++i]);
  }
  if (shotsDir) fs.mkdirSync(shotsDir, { recursive: true });

  const { chromium } = loadPlaywright();
  const server = await serve();
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await launch(chromium);
  const problems = [], notes = [];

  const articles = fs.readdirSync(path.join(ROOT, "articles"))
    .filter(f => f.endsWith(".html") && f !== "index.html").map(f => "/articles/" + f);
  const pages = ["/", "/articles/", "/404.html", ...articles];

  for (const [w, h, mobile, label] of [[1280, 800, false, "laptop"], [390, 844, true, "phone"]]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: mobile });
    const page = await ctx.newPage();
    let current = "";
    page.on("request", r => {
      const u = new URL(r.url());
      if (/^https?:$/.test(u.protocol) && u.hostname !== "127.0.0.1") problems.push(`${label} ${current}: contacts another website (${u.hostname})`);
    });
    page.on("response", r => {
      if (r.status() >= 400) {
        problems.push(`${label} ${current}: failed to load ${r.url().replace(base, "")} (${r.status()})`);
      }
    });
    page.on("pageerror", e => problems.push(`${label} ${current}: script error: ${e.message}`));

    for (const p of pages) {
      current = p;
      await page.goto(base + p);
      await page.waitForLoadState("networkidle");
      const r = await page.evaluate(async () => {
        await document.fonts.ready;
        return {
          width: document.documentElement.scrollWidth,
          fonts: [...document.fonts].filter(f => f.status === "loaded").length,
          brokenImages: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute("src")),
          article: !!document.querySelector("main.article-body"),
          nav: !!document.querySelector(".article-nav"),
        };
      });
      if (r.width > w) problems.push(`${label} ${p}: wider than the screen (${r.width}px on a ${w}px screen)`);
      if (r.fonts === 0) problems.push(`${label} ${p}: the site's fonts did not load`);
      if (r.brokenImages.length) problems.push(`${label} ${p}: images not loading: ${r.brokenImages.join(", ")}`);
      if (r.article && !r.nav) problems.push(`${label} ${p}: Earlier/Later links missing`);
    }

    if (label === "laptop") {
      await page.goto(base + "/articles/");
      const counts = {};
      for (const s of ["general-commercial", "corporate-ma", "regulatory", "all"]) {
        await page.click(`button[data-filter-subject="${s}"]`);
        counts[s] = await page.evaluate(() =>
          [...document.querySelectorAll(".archive-list li")].filter(l => !l.classList.contains("hidden")).length);
      }
      if (counts["general-commercial"] + counts["corporate-ma"] + counts["regulatory"] !== counts.all
          || counts.all !== articles.length) {
        problems.push(`archive filters do not add up: ${JSON.stringify(counts)}, ${articles.length} articles`);
      }
    }
    await ctx.close();
  }

  // The home page must fit the window, footer included, on laptops and monitors.
  for (const [w, h, label] of HOME_WINDOWS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const page = await ctx.newPage();
    await page.goto(base + "/");
    await page.waitForLoadState("networkidle");
    const r = await page.evaluate(async () => {
      await document.fonts.ready;
      // widest gap between words on any full line of justified text, in ems
      let worst = 0;
      for (const para of document.querySelectorAll("main .section-block p")) {
        const clone = para.cloneNode(true);
        para.after(clone); para.style.display = "none";
        const walker = document.createTreeWalker(clone, NodeFilter.SHOW_TEXT);
        const texts = []; while (walker.nextNode()) texts.push(walker.currentNode);
        for (const t of texts) {
          const frag = document.createDocumentFragment();
          t.textContent.split(/(\s+)/).forEach(x => {
            if (!x || /^\s+$/.test(x)) frag.appendChild(document.createTextNode(x));
            else { const s = document.createElement("span"); s.textContent = x; frag.appendChild(s); }
          });
          t.replaceWith(frag);
        }
        const lines = {};
        clone.querySelectorAll("span").forEach(s => {
          const b = s.getBoundingClientRect(); (lines[Math.round(b.top)] = lines[Math.round(b.top)] || []).push(b);
        });
        const keys = Object.keys(lines).map(Number).sort((a, b) => a - b);
        const size = parseFloat(getComputedStyle(para).fontSize);
        keys.slice(0, -1).forEach(k => {
          const bs = lines[k]; if (bs.length < 2) return;
          let gap = 0; for (let i = 1; i < bs.length; i++) gap += bs[i].left - bs[i - 1].right;
          worst = Math.max(worst, gap / (bs.length - 1) / size);
        });
        clone.remove(); para.style.display = "";
      }
      return {
        over: document.documentElement.scrollHeight - innerHeight,
        text: parseFloat(getComputedStyle(document.querySelector(".section-block p")).fontSize),
        worst,
      };
    });
    if (r.over > 0) problems.push(`home page: needs scrolling in a ${w}x${h} window (${label}) by ${r.over}px`);
    if (r.worst > 1.2) notes.push(`home page: a justified line has wide word gaps in a ${w}x${h} window (${label})`);
    await ctx.close();
  }

  if (shotsDir) {
    const shots = [["home-laptop", "/", 1440, 780, false], ["home-phone", "/", 390, 844, true]];
    for (const p of shotPages) {
      const name = path.basename(p, ".html") || "page";
      shots.push([name + "-laptop", p, 1440, 900, false], [name + "-phone", p, 390, 844, true]);
    }
    for (const [name, p, w, h, mobile] of shots) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: mobile });
      const page = await ctx.newPage();
      await page.goto(base + p);
      await page.waitForLoadState("networkidle");
      await page.screenshot({ path: path.join(shotsDir, name + ".png"), fullPage: mobile });
      await ctx.close();
    }
    console.log(`Screenshots saved in ${shotsDir}`);
  }

  await browser.close();
  server.close();

  const unique = [...new Set(problems)];
  if (notes.length) { console.log(`${notes.length} note(s):`); notes.forEach(n => console.log(" -", n)); }
  if (unique.length) {
    console.log(`${unique.length} problem(s) found:`);
    unique.forEach(p => console.log(" -", p));
    process.exit(1);
  }
  console.log(`No problems found (${pages.length} pages at laptop and phone size; home page at ${HOME_WINDOWS.length} window sizes).`);
}

main().catch(e => { console.error(e); process.exit(2); });
