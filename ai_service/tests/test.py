import asyncio
import json
import os
import re
from playwright.async_api import async_playwright

BRIGHT_DATA_WS = (
    "wss://brd-customer-hl_65057f24-zone-scraping_browser1:"
    "Your_Password_here"
    "@brd.superproxy.io:9222"
)

FLIPKART_URL = (
    "https://www.flipkart.com/"
    "puma-glidepacer-running-shoes-men/"
    "p/itm5ee7dfe134f1a"
    "?pid=SHOHPPYFYBAVVPGZ"
    "&marketplace=FLIPKART"
)


PRICE_JS = r"""
() => {
    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
        try {
            let data = JSON.parse(s.textContent);
            data = Array.isArray(data) ? data : [data];
            for (const d of data) {
                const offers = d.offers || (d['@graph'] || []).map(g => g.offers).find(Boolean);
                const o = Array.isArray(offers) ? offers[0] : offers;
                if (o && o.price) return Number(o.price);
            }
        } catch (e) {}
    }
    const el = [...document.querySelectorAll('div')].find(
        e => e.children.length === 0 && /^₹[\d,]+$/.test(e.innerText.trim()));
    return el ? Number(el.innerText.replace(/[^\d]/g, '')) : null;
}
"""

SIZES_JS = r"""
() => [...document.querySelectorAll('a[href*="swatchAttr=size"]')].map(a => {
    const box = a.firstElementChild;
    const cs = box ? getComputedStyle(box) : null;
    const labelEl = a.querySelector('div');
    const line = a.querySelector('div[style*="height: 1px"]');
    const lcs = line ? getComputedStyle(line) : null;
    return {
        size: labelEl?.innerText.trim(),
        pid: new URL(a.href, location.origin).searchParams.get('pid'),
        textColor: labelEl && getComputedStyle(labelEl).color,
        opacity: cs && cs.opacity,
        lineColor: lcs && lcs.borderColor,
        lineBg: lcs && lcs.backgroundColor,
    };
})
"""

def looks_unavailable(s):
    def visible(c):
        return c and c not in ("rgba(0, 0, 0, 0)", "transparent")
    if visible(s["lineColor"]) or visible(s["lineBg"]):
        return True
    if s["opacity"] and float(s["opacity"]) < 1:
        return True
    if s["textColor"] and s["textColor"] != "rgb(51, 51, 51)":
        return True
    return False

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(BRIGHT_DATA_WS)
        page = await browser.new_page()
        await page.goto(FLIPKART_URL, wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_selector('a[href*="swatchAttr=size"]', timeout=30000)

        price = await page.evaluate(PRICE_JS)
        sizes = await page.evaluate(SIZES_JS)

        for s in sizes:
            s["available"] = not looks_unavailable(s)
            print(f"Size {s['size']:>3} | available={s['available']} | pid={s['pid']}")

        print("\nAvailable sizes:", [s["size"] for s in sizes if s["available"]])
        print("Price:", price)

        await browser.close()

asyncio.run(main())