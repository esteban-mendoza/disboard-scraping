"""
This module contains a Scrapy spider that crawls the Disboard website
starting from the /servers endpoint.
"""

import redis

from disboard.commons.constants import DISBOARD_URL, WEBCACHE_URL
from disboard.commons.helpers import (
    extract_disboard_server_items,
    request_next_url,
    request_all_tag_urls,
    request_all_category_urls,
)
from scrapy_redis.spiders import RedisSpider


class ServersSpider(RedisSpider):
    """
    This spider crawls Disboard server listings using
    the "redis_key" queue in Redis.
    """

    name: str = "servers"
    redis_key: str = "servers:start_urls"
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
        if self.settings.get("FILTER_BY_LANGUAGE"):
            return f"?fl={self.settings.get('SELECTED_LANGUAGE')}"
        else:
            return ""

    @property
    def base_url(self):
        return f"{self.page_iterator_prefix}{DISBOARD_URL}"

    def start_requests(self):
        """
        If the START_FROM_BEGINNING flag is True, delete all the associated
        keys in Redis and pushes the start URL of the /servers endpoint to
        the Redis `redis_key` queue.

        If the flag is False, the spider will start from the last URL in the
        Redis queue of requests.
        """
        if self.settings.get("START_FROM_BEGINNING"):
            # Create a Redis connection
            r = redis.Redis(self.settings.get("REDIS_URL"))

            # Delete all 'servers' keys
            for key in r.scan_iter(f"{self.name}:*"):
                r.delete(key)

            # Push the /servers URL to the queue
            start_url = f"{self.base_url}/servers{self.language_postfix}"
            r.lpush(self.redis_key, start_url)

            # Close the connection
            r.close()

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
