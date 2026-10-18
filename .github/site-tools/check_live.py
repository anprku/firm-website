"""Check the live website, apklaw.in, as a visitor would reach it.

Run from the repository root:  python3 .github/site-tools/check_live.py
(or with --base http://127.0.0.1:8000 to try it against a local copy).

Needs only Python 3. It checks that the home page, the archive, the feed and
every page listed in the sitemap answer normally over a secure (https)
connection; that the plain http address forwards to https; that the security
certificate is valid and not close to expiring; and that the live site has
the latest published version (its sitemap matches the one in the repository).

Exit code 0 means no problems; 1 means at least one problem was found.
"""

import os
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

HOST = "apklaw.in"
problems, notes = [], []


def fetch(url, follow=True):
    req = urllib.request.Request(url, headers={"User-Agent": "apklaw-site-check"})
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    with opener.open(req, timeout=30) as r:
        return r.status, r.geturl(), r.read()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def status_of(url):
    try:
        status, final, body = fetch(url)
        return status, final, body
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, url, body
    except Exception as e:  # network failure, bad certificate, timeout
        return None, url, str(e).encode()


def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(root)
    base = f"https://{HOST}"
    if "--base" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1].rstrip("/")
    live = base == f"https://{HOST}"

    # The pages every visitor relies on, plus everything in the sitemap.
    repo_sitemap = open("sitemap.xml", encoding="utf-8").read()
    urls = ["/", "/articles/", "/feed.xml", "/sitemap.xml", "/robots.txt", "/css/styles.css"]
    urls += [re.sub(r"^https://[^/]+", "", u) for u in re.findall(r"<loc>([^<]+)</loc>", repo_sitemap)]
    seen = set()
    for path in urls:
        if path in seen:
            continue
        seen.add(path)
        status, final, body = status_of(base + path)
        if status is None:
            problems.append(f"{path}: could not be reached ({body.decode(errors='replace')[:120]})")
        elif status != 200:
            problems.append(f"{path}: answered with error {status}")
        elif live and not final.startswith(f"https://{HOST}/"):
            problems.append(f"{path}: ended up at {final} instead of the site")

    # A page that doesn't exist should show the site's own "not found" page.
    status, _, body = status_of(base + "/this-page-does-not-exist")
    if status != 404 or b"does not exist" not in body:
        problems.append(f"a missing page answered with {status} rather than the site's 404 page")

    # Is the live site the latest published version?
    status, _, body = status_of(base + "/sitemap.xml")
    if status == 200 and body.decode("utf-8", errors="replace") != repo_sitemap:
        notes.append("the live sitemap differs from the repository's. The site may still be "
                     "updating after a recent change; if this persists, check GitHub Pages.")

    if live:
        # http should forward to https
        try:
            fetch(f"http://{HOST}/", follow=False)
            problems.append("http://apklaw.in does not forward to https. Turn on 'Enforce HTTPS' "
                            "in the repository's Pages settings.")
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location", "")
            if e.code not in (301, 302, 307, 308) or not loc.startswith("https://"):
                problems.append(f"http://apklaw.in answered {e.code} without forwarding to https")
        except Exception as e:
            problems.append(f"http://apklaw.in could not be reached ({e})")

        # certificate
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((HOST, 443), timeout=30) as sock:
                with ctx.wrap_socket(sock, server_hostname=HOST) as tls:
                    cert = tls.getpeercert()
            expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days = (expires - datetime.now(timezone.utc)).days
            if days < 14:
                problems.append(f"the security certificate expires in {days} days (GitHub normally "
                                "renews it automatically; check the Pages settings)")
        except Exception as e:
            problems.append(f"the security certificate could not be checked ({e})")

    for n in notes:
        print("Note:", n)
    if problems:
        print(f"{len(problems)} problem(s) found on {base}:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print(f"No problems found ({len(seen)} addresses on {base} answered normally).")


if __name__ == "__main__":
    main()
