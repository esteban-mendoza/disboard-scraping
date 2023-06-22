from disboard.items import DisboardServerItem
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
            platform_link = server_info.css(".server-name a::attr(href)").get()
            guild_id = platform_link.split("/")[-1]
            server_name = server_info.css(".server-name a::text").get().strip()

            server_description = "".join(
                server_body.css(".server-description::text").getall()
            ).strip()

            data_ids = server_body.css(".tag::attr(data-id)").getall()
            tags = server_body.css(".tag::attr(title)").getall()
            tags = [{key: value} for key, value in zip(data_ids, tags)]

            category = server_info.css(".server-category::text").get().strip()
            yield DisboardServerItem(
                scrape_time=scrape_time,
                platform_link=platform_link,
                guild_id=guild_id,
                server_name=server_name,
                server_description=server_description,
                tags=tags,
                category=category,
            )

    async def error_handler(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.screenshot(path=f"screenshot-{page.url}.png")
        await page.close()
