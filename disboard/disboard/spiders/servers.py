from disboard.items import ServerItem
from datetime import datetime
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
        server_info_selectorlist = response.css(".server-info")
        server_body_selectorlist = response.css(".server-body")

        response_date = response.headers["Date"].decode()
        scrape_time = datetime.strptime(
            response_date, "%a, %d %b %Y %H:%M:%S %Z"
        ).timestamp()

        for server_info, server_body in zip(
            server_info_selectorlist, server_body_selectorlist
        ):
            server_item = ServerItem()

            server_item["scrape_time"] = scrape_time
            server_item["platform_link"] = server_info.css(
                ".server-name a::attr(href)"
            ).get()
            server_item["guild_id"] = server_item["platform_link"].split("/")[-1]
            server_item["server_name"] = server_info.css(".server-name a::text").get()

            server_item["server_description"] = "".join(
                server_body.css(".server-description::text").getall()
            ).strip()

            data_ids = server_body.css(".tag::attr(data-id)").getall()
            tags = server_body.css(".tag::attr(title)").getall()
            server_item["tags"] = list(zip(data_ids, tags))

            server_item["category"] = server_info.css(".server-category::text").get()
            yield server_item

    async def error_handler(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.screenshot(path=f"screenshot-{page.url}.png")
        await page.close()
