from playwright.async_api import async_playwright


class BrightDataBrowser:

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.playwright = None
        self.browser = None

    async def connect(self):
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.connect_over_cdp(
            self.ws_url
        )

        return self.browser

    async def new_page(self):
        if not self.browser:
            raise RuntimeError("Browser is not connected")

        return await self.browser.new_page()

    async def close(self):
        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()