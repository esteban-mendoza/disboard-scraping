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
from logging import getLogger, INFO
from scrapy_redis.spiders import RedisSpider


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
    def page_iterator_prefix(self):
        if self.settings.get("USE_WEB_CACHE"):
            return WEBCACHE_URL
        else:
            return ""

    @property
    def language_postfix(self):
        language = self.settings.get("LANGUAGE")
        if language == "":
            return ""
        else:
            return f"?fl={language}"

    def parse(self, response):
        """
        Parse the response and extract DisboardServerItems.
        Follow the pagination links to request the next page.

        If no DisboardServerItems are found, stops parsing the response.
        """
        n_of_server_items = count_disboard_server_items(response)

        self.logger.log(
            INFO, f"Found {n_of_server_items} DisboardServerItems in {response.url}"
        )

        if n_of_server_items > 0:
            yield from extract_disboard_server_items(response)

            if n_of_server_items >= 12 and has_pagination_links(response):
                if self.settings.get("FOLLOW_PAGINATION_LINKS"):
                    yield from request_next_url(self, response)

            if self.settings.get("FOLLOW_CATEGORY_LINKS"):
                yield from request_all_category_urls(self, response)

            if n_of_server_items >= 8:
                if self.settings.get("FOLLOW_TAG_LINKS"):
                    yield from request_all_tag_urls(self, response)
