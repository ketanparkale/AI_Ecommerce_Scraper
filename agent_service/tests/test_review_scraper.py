import asyncio

from app.clients.review_scraper_client import ReviewScraperClient


async def test_review_scraper_client():

    client = ReviewScraperClient()

    product_url = "https://www.flipkart.com/cult-grace-walking-shoes-breathable-knitted-upper-enhanced-cushioning-grip-women/p/itm1ff0105e41af8?pid=SHOHH875P8KHZAJM&lid=LSTSHOHH875P8KHZAJMFITJOL&hl_lid=&marketplace=FLIPKART&fm=eyJ3dHAiOiJyZWNvIiwicHJwdCI6InBwIiwibWlkIjoicHJvZHVjdFJlY29tbWVuZGF0aW9uL3NpbWlsYXIifQ%3D%3D&pageUID=1794130379845"

    response = await client.scrape(product_url)

    print("\n========== REVIEW SCRAPER RESPONSE ==========")
    print(response)

    print("\n========== RESPONSE TYPE ==========")
    print(type(response))

    print("\n========== RESPONSE KEYS ==========")
    print(response.keys())


if __name__ == "__main__":
    asyncio.run(test_review_scraper_client())