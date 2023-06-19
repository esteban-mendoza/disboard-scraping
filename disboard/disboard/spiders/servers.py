from disboard.items import ServerItem
import scrapy
from scrapy_playwright.page import PageMethod

WEBCACHE_URL = "https://webcache.googleusercontent.com/search?q=cache:"


class ServersSpider(scrapy.Spider):
    name = "servers"

    def start_requests(self):
        url = f"{WEBCACHE_URL}https://disboard.org/servers"
        yield scrapy.Request(
            url=url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod("wait_for_selector", ".server-name a"),
                ],
                errback=self.error_handler,
            ),
        )

    def parse(self, response):
        for server in response.css(".server-info"):
            server_item = ServerItem()
            server_item["scrape_time"] = response.headers["Date"].decode()
            server_item["platform_link"] = server.css(
                ".server-name a::attr(href)"
            ).get()
            server_item["guild_id"] = server_item["platform_link"].split("/")[-1]
            server_item["server_name"] = server.css(".server-name a::text").get()
            server_item["category"] = server.css(".server-category::text").get()
            yield server_item

    async def error_handler(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.screenshot(path=f"screenshot-{page.url}.png")
        await page.close()
