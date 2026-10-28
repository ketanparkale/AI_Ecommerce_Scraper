from .brightdata_browser import BrightDataBrowser
from urllib.parse import urlparse, parse_qs

PRICE_JS = r"""
() => {
    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
        try {
            let data = JSON.parse(s.textContent);

            data = Array.isArray(data) ? data : [data];

            for (const d of data) {
                const offers =
                    d.offers ||
                    (d['@graph'] || [])
                        .map(g => g.offers)
                        .find(Boolean);

                const offer = Array.isArray(offers)
                    ? offers[0]
                    : offers;

                if (offer && offer.price) {
                    return Number(offer.price);
                }
            }

        } catch (e) {
            // Ignore invalid JSON-LD blocks
        }
    }

    // Fallback: find a visible ₹ price in the page
    const element = [...document.querySelectorAll('div')].find(
        element =>
            element.children.length === 0 &&
            /^₹[\d,]+$/.test(element.innerText.trim())
    );

    return element
        ? Number(element.innerText.replace(/[^\d]/g, ''))
        : null;
}
"""


SIZES_JS = r"""
() => {
    return [
        ...document.querySelectorAll(
            'a[href*="swatchAttr=size"]'
        )
    ].map(a => {

        const box = a.firstElementChild;
        const boxStyle = box
            ? getComputedStyle(box)
            : null;

        const labelElement = a.querySelector('div');

        const line = a.querySelector(
            'div[style*="height: 1px"]'
        );

        const lineStyle = line
            ? getComputedStyle(line)
            : null;

        return {
            size: labelElement?.innerText.trim() || null,

            pid: new URL(
                a.href,
                location.origin
            ).searchParams.get('pid'),

            textColor:
                labelElement
                    ? getComputedStyle(labelElement).color
                    : null,

            opacity:
                boxStyle
                    ? boxStyle.opacity
                    : null,

            lineColor:
                lineStyle
                    ? lineStyle.borderColor
                    : null,

            lineBg:
                lineStyle
                    ? lineStyle.backgroundColor
                    : null
        };
    });
}
"""


def looks_unavailable(size: dict) -> bool:

    def visible(color: str | None) -> bool:
        return (
            color is not None
            and color not in (
                "rgba(0, 0, 0, 0)",
                "transparent"
            )
        )

    if visible(size["lineColor"]):
        return True

    if visible(size["lineBg"]):
        return True

    if size["opacity"] is not None:
        try:
            if float(size["opacity"]) < 1:
                return True
        except ValueError:
            pass

    if (
        size["textColor"] is not None
        and size["textColor"] != "rgb(51, 51, 51)"
    ):
        return True

    return False


class FlipkartScraper:

    def __init__(self, browser: BrightDataBrowser):
        self.browser = browser

    async def scrape_product(self, url: str) -> dict:
        page = await self.browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_selector(
                'a[href*="swatchAttr=size"]', timeout=30000
            )

            title = await page.title()
            price = await page.evaluate(PRICE_JS)
            sizes = await page.evaluate(SIZES_JS)

            current_pid = parse_qs(urlparse(url).query).get("pid", [None])[0]

            for s in sizes:
                s["available"] = not looks_unavailable(s)
                # The page price belongs only to the PID currently loaded
                s["price"] = price if s["pid"] == current_pid else None

            return {"url": url, "title": title, "sizes": sizes}
        finally:
            await page.close()
