"""
This module contains a Scrapy spider that crawls the Disboard website
starting from the /servers endpoint.
"""

from disboard.commons.constants import DISBOARD_URL, WEBCACHE_URL
from disboard.commons.helpers import (
    count_disboard_server_items,
    has_pagination_links,
    extract_disboard_server_items,
    request_next_url,
    request_all_tag_urls,
    request_all_category_urls,
)
from disboard.items import DisboardServerItem
from logging import getLogger, DEBUG, WARNING
from scrapy.http import Request, Response
from scrapy_redis.spiders import RedisSpider
from typing import Generator, Union


class ServersSpider(RedisSpider):
    """
    This spider crawls Disboard server listings using
    the "redis_key" queue in Redis.
    """

    logger = getLogger(__name__)

    name: str = "servers"
    base_url: str = DISBOARD_URL
    allowed_domains: list = ["disboard.org", "webcache.googleusercontent.com"]

    # Max idle time (in seconds) before the spider stops checking redis and shuts down
    max_idle_time: float = 7

    @property
    def page_iterator_prefix(self) -> str:
        if self.settings.get("USE_WEB_CACHE"):
            return WEBCACHE_URL
        else:
            return ""

    @property
    def language_postfix(self) -> str:
        language = self.settings.get("LANGUAGE")
        if language == "":
            return ""
        else:
            return f"?fl={language}"

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

            if n_of_server_items > 0:
                yield from extract_disboard_server_items(response)
                yield from self._handle_pagination_links(n_of_server_items, response)
                yield from self._handle_category_links(response)
                yield from self._handle_tag_links(n_of_server_items, response)

        except ValueError:
            self._log_disboard_server_items(0, response, WARNING)

    def _log_disboard_server_items(
        self, n_of_server_items: int, response: Response, log_level: int = DEBUG
    ) -> None:
        self.logger.log(
            log_level,
            f"Found {n_of_server_items} DisboardServerItems in {response.url}",
        )
        if n_of_server_items == 0:
            self.logger.log(DEBUG, f"Response body: {response.body}")

    def _handle_pagination_links(
        self, n_of_server_items: int, response: Response
    ) -> Generator[DisboardServerItem, None, None]:
        if (
            n_of_server_items >= 12
            and has_pagination_links(response)
            and self.settings.get("FOLLOW_PAGINATION_LINKS")
        ):
            yield from request_next_url(self, response)

    def _handle_category_links(
        self, response: Response
    ) -> Generator[DisboardServerItem, None, None]:
        if self.settings.get("FOLLOW_CATEGORY_LINKS"):
            yield from request_all_category_urls(self, response)

    def _handle_tag_links(
        self, n_of_server_items: int, response: Response
    ) -> Generator[DisboardServerItem, None, None]:
        if n_of_server_items >= 8 and self.settings.get("FOLLOW_TAG_LINKS"):
            yield from request_all_tag_urls(self, response)
