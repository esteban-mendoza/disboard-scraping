"""
This module contains a Scrapy spider that crawls the Disboard website
starting from the /servers endpoint, and follows pagination and tag links.
"""

from typing import Any, Dict
from disboard.commons.helpers import (
    extract_disboard_server_items,
    request_next_url,
    request_all_tag_urls,
    request_all_category_urls,
    request_all_filter_by_language,
)
from disboard.commons.constants import DISBOARD_URL, WEBCACHE_URL
import scrapy
from scrapy_playwright.page import PageMethod


class ServersSpider(scrapy.Spider):
    """
    This spider crawls Disboard starting by the /servers endpoint,
    following pagination and tag links.
    """

    name: str = "servers"
    default_request_args: Dict[str, Any] = {
        "playwright": True,
    }

    @property
    def page_iterator_prefix(self):
        if self.settings.get("USE_WEB_CACHE"):
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
        url = f"{self.base_url}/servers/5"
        yield scrapy.Request(
            url=url, meta={**self.default_request_args, "errback": self.error_handler}
        )

    def parse(self, response):
        """
        Parse the response and extract DisboardServerItems.
        Follow the pagination links to request the next page.
        """
        yield from extract_disboard_server_items(response)

        if self.settings.get("FOLLOW_PAGINATION_LINKS"):
            yield from request_next_url(self, response)

        if self.settings.get("FOLLOW_TAG_LINKS"):
            yield from request_all_tag_urls(self, response)

        if self.settings.get("FOLLOW_CATEGORY_LINKS"):
            yield from request_all_category_urls(self, response)

        if self.settings.get("FILTER_BY_LANGUAGE"):
            yield from request_all_filter_by_language(self, response)

    async def error_handler(self, failure):
        """
        Handle errors that occur during the crawling process.
        Capture a screenshot and close the page.
        """
        page = failure.request.meta["playwright_page"]
        await page.close()
