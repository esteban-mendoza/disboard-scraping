"""
This module contains a Scrapy spider that crawls the Disboard website
starting from the /servers endpoint.
"""

from disboard.commons.constants import DISBOARD_URL, WEBCACHE_URL
from disboard.commons.helpers import (
    blocked_by_cloudflare,
    is_server_listing,
    count_disboard_server_items,
    has_pagination_links,
    extract_disboard_server_items,
    request_next_url,
    request_all_tag_urls,
    request_all_category_urls,
)
from disboard.items import DisboardServerItem
from logging import getLogger, INFO, DEBUG, WARNING
from scrapy.http import Request, Response
from scrapy_redis.spiders import RedisSpider
from typing import Generator, Union


class ServersSpider(RedisSpider):
    """
    This spider crawls Disboard server listings using the /servers endpoint.
    """

    logger = getLogger(__name__)

    name: str = "servers"
    base_url: str = DISBOARD_URL
    allowed_domains: list = ["disboard.org", "webcache.googleusercontent.com"]

    # Max idle time (in seconds) before the spider stops checking redis and shuts down
    max_idle_time: float = 120

    @property
    def url_prefix(self) -> str:
        if self.settings.getbool("USE_WEB_CACHE"):
            return WEBCACHE_URL
        else:
            return ""

    @property
    def language(self) -> str:
        return self.settings.get("LANGUAGE")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        getLogger("scrapy.core.scraper").setLevel(INFO)

    def parse(
        self, response: Response
    ) -> Generator[Union[DisboardServerItem, Request], None, None]:
        """
        Parse the response and extract DisboardServerItems.
        Follow the pagination links to request the next page.

        If no DisboardServerItems are found, stops parsing the response.
        """
        try:
            n_of_server_items = count_disboard_server_items(response)
            self._log_disboard_server_items(n_of_server_items, response)

            if n_of_server_items == 0:
                yield from self._handle_0_server_items(response)

            if n_of_server_items > 0:
                yield from extract_disboard_server_items(response)
                yield from self._handle_pagination_links(n_of_server_items, response)

            yield from self._handle_category_links(response)
            yield from self._handle_tag_links(response)

        except ValueError:
            self._log_disboard_server_items(0, response, WARNING)

    def _handle_0_server_items(
        self, response: Response
    ) -> Generator[Request, None, None]:
        """
        If the response has been blocked by Cloudflare, request the same URL again.
        """
        if blocked_by_cloudflare(response):
            self.logger.warning(
                f"Blocked by Cloudflare: <{response.status} {response.url}>"
            )
            self.logger.debug(f"Retrying: {response.url}")
            request = response.request.replace(
                dont_filter=True, priority=response.request.priority - 10
            )
            yield request

        if not is_server_listing(response):
            self.logger.debug(
                f"Response is not a server listing: <{response.status} {response.url}>"
            )
            self.logger.debug(f"Response body: {response.body}")

    def _handle_pagination_links(
        self, n_of_server_items: int, response: Response
    ) -> Generator[Request, None, None]:
        """
        If there are more than 5 DisboardServerItems in the response,
        and the response has pagination links, and the spider is configured
        to follow pagination links, request the next page.

        When the response has less than 5 DisboardServerItems,
        the next page will probably have 0 DisboardServerItems.
        """
        if (
            n_of_server_items >= 5
            and has_pagination_links(response)
            and self.settings.getbool("FOLLOW_PAGINATION_LINKS")
        ):
            yield from request_next_url(self, response)

    def _handle_category_links(
        self, response: Response
    ) -> Generator[Request, None, None]:
        """
        If the spider is configured to follow category links,
        request all category links in the response.
        """
        if self.settings.getbool("FOLLOW_CATEGORY_LINKS"):
            yield from request_all_category_urls(self, response)

    def _handle_tag_links(self, response: Response) -> Generator[Request, None, None]:
        """
        If the spider is configured to follow tag links, request all tag links
        in the response.

        These tag links might be in the "similar-tags" section of the response.
        """
        if self.settings.getbool("FOLLOW_TAG_LINKS"):
            yield from request_all_tag_urls(self, response)

    def _log_disboard_server_items(
        self, n_of_server_items: int, response: Response, log_level: int = DEBUG
    ) -> None:
        self.logger.log(
            log_level,
            f"Found {n_of_server_items} DisboardServerItems in {response.url}",
        )
        if n_of_server_items == 0:
            self.logger.debug(f"Response body: {response.body}")
