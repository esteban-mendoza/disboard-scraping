"""
This is the entry point for a single spider running in a container.
"""

import os
import redis

from typing import List
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from disboard.commons.constants import DISBOARD_URL, WEBCACHE_URL
from disboard.spiders.servers import ServersSpider


def get_start_urls() -> List[str]:
    """
    This function returns the start urls for the spider.

    It uses the LANGUAGE and USE_WEBCACHE environment variables
    to determine the start urls.
    """
    language = os.environ["LANGUAGE"]
    base_url = DISBOARD_URL
    prefix = WEBCACHE_URL if os.environ["USE_WEBCACHE"] == "True" else ""

    by_none = f"{prefix}{base_url}/servers"
    by_language = f"{prefix}{base_url}/servers?fl={language}"
    by_language_and_members = (
        f"{prefix}{base_url}/servers?fl={language}&sort=member_count"
    )

    return [
        by_none,
        by_language,
        by_language_and_members,
    ]


def restart_or_continue_job() -> None:
    """
    If the RESTART_JOB environment variable is set to True, then
    the job will be restarted. Otherwise, the job will continue.
    """

    if os.environ["RESTART_JOB"] == "False":
        return

    redis_url = os.environ["REDIS_URL"]
    spider_name = os.environ["SPIDER_NAME"]
    start_urls = get_start_urls()

    client = redis.Redis.from_url(redis_url)
    with client.pipeline() as pipe:
        pipe.delete(f"{spider_name}:dupefilter")
        pipe.delete(f"{spider_name}:requests")
        pipe.delete(f"{spider_name}:guild_id")
        for url in start_urls:
            pipe.lpush(f"{spider_name}:start_urls", url)
        pipe.execute()

    client.close()


def run_named_spider() -> None:
    class NamedSpider(ServersSpider):
        name = os.environ["SPIDER_NAME"]

    process = CrawlerProcess(get_project_settings())
    process.crawl(NamedSpider)
    process.start()


if __name__ == "__main__":
    restart_or_continue_job()
    run_named_spider()
