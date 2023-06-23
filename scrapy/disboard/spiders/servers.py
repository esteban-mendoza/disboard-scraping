"""
This module contains a Scrapy spider that crawls the Disboard website
starting from the /servers endpoint, and follows the pagination links.
"""

from typing import Any, Dict
from disboard.commons.helpers import extract_disboard_server_items
from disboard.commons.constants import DISBOARD_URL, WEBCACHE_URL
import scrapy
from scrapy_playwright.page import PageMethod


class ServersSpider(scrapy.Spider):
    """
    This spider crawls Disboard starting by the /servers endpoint
    and following the pagination links.
    """

    name: str = "servers"
    default_request_args: Dict[str, Any] = {
        "playwright": True,
        "playwright_page_methods": [
            PageMethod("wait_for_selector", ".server-name a"),
        ],
    }

    @property
    def page_iterator_prefix(self):
        if self.settings.get("USE_WEB_CACHE", True):
            return WEBCACHE_URL
        else:
            return ""

    @property
    def base_url(self):
        return f"{self.page_iterator_prefix}{DISBOARD_URL}"

    def start_requests(self):
        """
        Generate the initial request to the /servers endpoint.
        """
        url = f"{self.base_url}/servers"
        yield scrapy.Request(
            url=url, meta={**self.default_request_args, "errback": self.error_handler}
        )

    def parse(self, response):
        """
        Parse the response and extract DisboardServerItems.
        Follow the pagination links to request the next page.
        """
        yield from extract_disboard_server_items(response)

        next_url = response.css(".next a::attr(href)").get()
        if next_url is not None:
            next_url = f"{self.page_iterator_prefix}{response.urljoin(next_url)}"
            yield scrapy.Request(
                url=next_url,
                meta={**self.default_request_args, "errback": self.error_handler},
            )

        tags = response.css(".tag::attr(title)").getall()
        for tag in tags:
            tag_url = f"{self.base_url}/servers/tag/{tag}"
            yield scrapy.Request(
                url=tag_url,
                meta={**self.default_request_args, "errback": self.error_handler},
            )

    async def error_handler(self, failure):
        """
        Handle errors that occur during the crawling process.
        Capture a screenshot and close the page.
        """
        page = failure.request.meta["playwright_page"]
        await page.screenshot(path=f"screenshot-{page.url}.png")
        await page.close()
