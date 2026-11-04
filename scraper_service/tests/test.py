#!/usr/bin/env python3
"""
Flipkart review scraper: give it a product link, get reviews as CSV + JSON.

Setup (once):
    pip install playwright
    playwright install chromium

Usage:
    python flipkart_reviews.py "<flipkart product or product-reviews URL>"
    python flipkart_reviews.py "<url>" --max 300 --sort latest --out myshoes
    python flipkart_reviews.py "<url>" --headless      # try only if the default (visible) mode works first

Notes:
- Runs a real Chromium window by default. Flipkart uses bot protection, and a visible
  browser with a persistent profile (./.fk_profile) is blocked far less often than headless.
- Parsing relies on the review text layout ("Review for: ...", "Helpful for N",
  "Verified Purchase"), NOT on Flipkart's auto-generated CSS class names, so it
  survives most front-end rebuilds.
- Keep volumes modest and check Flipkart's Terms of Use before commercial use.
"""
import argparse
import csv
import json
import re
import sys
import time
from datetime import date, timedelta
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Change this to scrape a different product, or pass a URL on the command line.
DEFAULT_URL = (
    "https://www.flipkart.com/v-guard-smart-pro-1200-mobile-app-control-3-year-warranty-pure-sine-wave-inverter/p/itm9ef83fc9eb2ec?pid=INVFE57AMFBUTGDU&lid=LSTINVFE57AMFBUTGDULEXV2A&hl_lid=&marketplace=FLIPKART&fm=eyJ3dHAiOiJhdGxhc19wbXVfdjUiLCJwcnB0IjoiaHAiLCJtaWQiOiJiZXN0c2VsbGVyL1UyUF9ERlkifQ%3D%3D&pageUID=1793629246183"
)



# ---------- URL handling ----------
def to_reviews_url(url: str) -> str:
    """Turn a /p/ product URL into its /product-reviews/ URL (keeps pid/lid query)."""
    u = urlparse(url.strip())
    if "flipkart.com" not in u.netloc:
        sys.exit("That doesn't look like a flipkart.com URL.")
    path = u.path
    if "/product-reviews/" in path:
        return url.strip()
    if "/p/" in path:
        path = path.replace("/p/", "/product-reviews/", 1)
        return urlunparse((u.scheme, u.netloc, path, "", u.query, ""))
    sys.exit("Expected a Flipkart product (/p/) or product-reviews URL.")


# ---------- In-page JS ----------
JS_COUNT = "() => (document.body.innerText.match(/Review for:/g) || []).length"

JS_SCROLL_DOWN = """
() => {
  const leaves = [...document.querySelectorAll('div,span')].filter(
    e => e.children.length === 0 && /^Review for:/.test(e.textContent.trim()));
  const last = leaves[leaves.length - 1];
  if (last) {
    last.scrollIntoView({ block: 'end' });
    let el = last;
    while (el) {
      if (el.scrollHeight > el.clientHeight + 50) el.scrollTop = el.scrollHeight;
      el = el.parentElement;
    }
  }
  const loader = [...document.querySelectorAll('div,span')].find(
    e => e.children.length === 0 && /Hang on, loading content/.test(e.textContent));
  if (loader) loader.scrollIntoView({ block: 'center' });
  window.scrollTo(0, document.body.scrollHeight);
}
"""

JS_EXPAND_MORE = """
() => {
  const re = /^(\\.{2,3}|…)?\\s*(read\\s+)?more$/i;
  const cands = [...document.querySelectorAll('span,div,a,button')]
    .filter(e => re.test(e.textContent.trim()));
  // keep only the innermost matches (no matching descendant)
  const inner = cands.filter(e => !cands.some(o => o !== e && e.contains(o)));
  let n = 0;
  for (const e of inner) { try { e.click(); n++; } catch (_) {} }
  return n;
}
"""

JS_EXTRACT = """
() => {
  const leaves = [...document.querySelectorAll('div,span')].filter(
    e => e.children.length === 0 && /^Review for:/.test(e.textContent.trim()));
  const out = [];
  for (const leaf of leaves) {
    let node = leaf;
    while (node.parentElement) {
      const p = node.parentElement;
      const n = ((p.innerText || '').match(/Review for:/g) || []).length;
      if (n > 1) break;
      node = p;
    }
    const imgs = [...node.querySelectorAll('img')]
      .map(i => i.currentSrc || i.src || '')
      .filter(s => s.includes('/blobio/'));
    out.push({ text: node.innerText || '', images: [...new Set(imgs)] });
  }
  const summary = (document.body.innerText.match(/[\\d,]+ ratings and [\\d,]+ reviews/) || [''])[0];
  return { blocks: out, summary };
}
"""


# ---------- Parsing ----------
DATE_RE = re.compile(r"^[·•\s]*(\d+)\s+(day|week|month|year)s?\s+ago$|^[·•\s]*(today|yesterday)$", re.I)
NUM_RE = re.compile(r"^\d(\.\d)?$")


def approx_date(rel: str):
    m = DATE_RE.match(rel.strip())
    if not m:
        return ""
    if m.group(3):
        d = date.today() - timedelta(days=1 if m.group(3).lower() == "yesterday" else 0)
        return d.isoformat()
    n, unit = int(m.group(1)), m.group(2).lower()
    days = {"day": 1, "week": 7, "month": 30, "year": 365}[unit] * n
    return (date.today() - timedelta(days=days)).isoformat()


def parse_block(text: str, images):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    try:
        v = next(i for i, l in enumerate(lines) if l.startswith("Review for:"))
    except StopIteration:
        return None

    # cut at the date line (everything after belongs to the next element)
    end = len(lines)
    for i in range(v + 1, len(lines)):
        if DATE_RE.match(lines[i]):
            end = i + 1
            break
    after = lines[v + 1:end]

    # rating + title sit just above "Review for:"
    before = [l for l in lines[:v] if l not in ("•", "·")]
    title = before[-1] if before else ""
    rating = ""
    if len(before) >= 2 and NUM_RE.match(before[-2]):
        rating = before[-2]
    elif before and NUM_RE.match(before[-1]):
        rating, title = before[-1], ""

    variant = lines[v][len("Review for:"):].strip()
    rel_date = after[-1] if after and DATE_RE.match(after[-1]) else ""
    verified = any(l.lower() == "verified purchase" for l in after)

    helpful = downvotes = ""
    h_idx = next((i for i, l in enumerate(after) if l.startswith("Helpful for")), None)
    if h_idx is not None:
        m = re.search(r"(\d+)", after[h_idx])
        helpful = m.group(1) if m else ""
        if h_idx + 1 < len(after) and after[h_idx + 1].isdigit():
            downvotes = after[h_idx + 1]

    # body / author / city = lines between variant and the "Helpful for" line
    pre = after[:h_idx] if h_idx is not None else after[:-1]
    author = city = ""
    if pre and pre[-1].startswith(","):
        city = pre[-1].lstrip(", ").strip()
        pre = pre[:-1]
        author = pre.pop().strip() if pre else ""
    elif pre and ", " in pre[-1] and len(pre[-1]) < 80:
        author, _, city = pre.pop().rpartition(", ")
    body = "\n".join(pre).replace("...more", "").strip()
    body = re.sub(r"\s*(read\s+)?less\s*$", "", body, flags=re.I).strip()
    if body.endswith("more") and body[:-4].rstrip().endswith("..."):
        body = body[:-4].rstrip().rstrip(".").strip()

    return {
        "rating": rating,
        "title": title,
        "review": body,
        "variant": variant,
        "author": author,
        "city": city,
        "verified_purchase": verified,
        "helpful": helpful,
        "not_helpful": downvotes,
        "posted_relative": rel_date,
        "posted_approx": approx_date(rel_date),
        "image_urls": " | ".join(images),
    }


MAX_PAGES = 60


def with_page(url, n):
    """Return url with ?page=n set (replacing any existing page param)."""
    u = urlparse(url)
    q = dict(parse_qsl(u.query))
    q["page"] = str(n)
    return urlunparse(u._replace(query=urlencode(q)))


def scroll_all(page, want):
    """Scroll the current page until no new reviews load. Returns how many are on the page."""
    stagnant, last = 0, -1
    while stagnant < 6:
        page.evaluate(JS_SCROLL_DOWN)
        page.keyboard.press("End")
        page.mouse.wheel(0, 3000)
        time.sleep(2)
        n = page.evaluate(JS_COUNT)
        print(f"\rreviews on this page: {n}", end="", file=sys.stderr, flush=True)
        if n >= want:
            break
        stagnant = stagnant + 1 if n == last else 0
        last = n
    print(file=sys.stderr)
    return n


def expand_all(page):
    for _ in range(5):
        if not page.evaluate(JS_EXPAND_MORE):
            break
        time.sleep(1)

# ---------- Main ----------
def scrape(url, max_reviews, sort, headless, profile):
    reviews, seen = [], set()
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            profile,
            headless=headless,
            viewport={"width": 1280, "height": 900},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        try:
            page.wait_for_function("() => (document.body.innerText.match(/Review for:/g)||[]).length > 0", timeout=25000)
        except PWTimeout:
            if headless:
                title = page.title()
                ctx.close()
                sys.exit(f"No reviews appeared (page title: {title!r}). Likely a captcha/block. "
                         f"Re-run without --headless.")
            print("\nNo reviews yet. If a captcha/verification is showing in the browser window, "
                  "solve it now. Waiting up to 3 minutes...", file=sys.stderr)
            try:
                page.wait_for_function(
                    "() => (document.body.innerText.match(/Review for:/g)||[]).length > 0",
                    timeout=180000)
            except PWTimeout:
                title = page.title()
                ctx.close()
                sys.exit(f"Still no reviews (page title: {title!r}). Blocked, or the product has no reviews.")

        if sort in ("latest", "positive", "negative"):
            try:
                page.get_by_text(sort.capitalize(), exact=True).first.click(timeout=5000)
                time.sleep(2)
            except Exception:
                print(f"(could not switch sort to {sort}; continuing with default)", file=sys.stderr)

        page.mouse.move(640, 450)  # wheel events go to whatever is under the cursor
        base_url = page.url        # keeps any sort setting Flipkart put in the URL
        summary, page_no = "", 1
        while len(reviews) < max_reviews and page_no <= MAX_PAGES:
            if page_no > 1:
                page.goto(with_page(base_url, page_no), wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_function(
                        "() => (document.body.innerText.match(/Review for:/g)||[]).length > 0",
                        timeout=20000)
                except PWTimeout:
                    print(f"\nNo reviews on page {page_no}; stopping.", file=sys.stderr)
                    break

            loaded = scroll_all(page, max_reviews - len(reviews))
            # temporary: put right after scroll_all(...) on page 1
            print(page.evaluate("""() => {
            const e = [...document.querySelectorAll('span,div,a,button')]
                .find(x => /more$/i.test(x.textContent.trim()) && x.textContent.trim().length < 12);
            return e ? e.outerHTML + '\\n--- parent ---\\n' + e.parentElement.outerHTML.slice(0, 600) : 'no match';
            }"""), file=sys.stderr)
            if page_no == 1 and loaded <= 10:
                print("\n(only 10 on page 1; saving debug_page.png)", file=sys.stderr)
                page.screenshot(path="debug_page.png")

            expand_all(page)
            data = page.evaluate(JS_EXTRACT)
            summary = summary or data.get("summary", "")

            new = 0
            for b in data["blocks"]:
                r = parse_block(b["text"], b["images"])
                if not r:
                    continue
                key = (r["author"], r["city"], r["title"], r["review"], r["variant"])
                if key in seen:
                    continue
                seen.add(key)
                reviews.append(r)
                new += 1
            print(f"page {page_no}: +{new} new ({len(reviews)} total)", file=sys.stderr)
            if new == 0:
                break
            page_no += 1
        ctx.close()
    return summary, reviews[:max_reviews]


def main():
    ap = argparse.ArgumentParser(description="Scrape Flipkart reviews from a product link.")
    ap.add_argument("url", nargs="?", default=DEFAULT_URL,
                    help="Flipkart product or reviews URL (default: the URL set at the top of this file)")
    ap.add_argument("--max", type=int, default=100, help="max reviews to collect (default 100)")
    ap.add_argument("--sort", choices=["default", "latest", "positive", "negative"], default="default")
    ap.add_argument("--out", default="flipkart_reviews", help="output file prefix")
    ap.add_argument("--headless", action="store_true", help="no visible window (more likely to be blocked)")
    ap.add_argument("--profile", default=".fk_profile", help="browser profile dir (keeps cookies)")
    a = ap.parse_args()

    summary, reviews = scrape(to_reviews_url(a.url), a.max, a.sort, a.headless, a.profile)
    if not reviews:
        sys.exit("Page loaded but no reviews could be parsed.")

    with open(f"{a.out}.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "reviews": reviews}, f, ensure_ascii=False, indent=2)
    with open(f"{a.out}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(reviews[0].keys()))
        w.writeheader()
        w.writerows(reviews)
    print(f"{summary}\nSaved {len(reviews)} reviews -> {a.out}.csv, {a.out}.json")


if __name__ == "__main__":
    main()