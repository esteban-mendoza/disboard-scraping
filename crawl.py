"""
This is the main entry point of the application.

The application is a Scrapy spider that crawls Disboard.org
and extracts information about Discord servers.

This file is a utility script that allows the user to run the spider
from the command line and override the default settings.

The default settings are stored in an .env file. The user can override
the default settings by passing command line arguments.
"""
import redis
import os

from argparse import ArgumentParser, Namespace
from dotenv import load_dotenv, find_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from disboard.spiders.servers import ServersSpider


def add_cli_arguments() -> ArgumentParser:
    """
    Add command line arguments and return the parser.
    """
    parser = ArgumentParser(description="Scrape Disboard.org")

    parser.add_argument(
        "--spider-name",
        help="The name of the spider. Note that this name will also be \
            used as the Redis' keys for queueing and filtering requests.\n\
            This name allows you to run multiple spiders with different settings \
            at the same time.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--use-web-cache",
        help="Use Google's web cache to get the HTML of the page",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--follow-pagination-links",
        help="Follow pagination links",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--follow-category-links",
        help="Follow category links",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--follow-tag-links",
        help="Follow tag links",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--concurrent-proxy-requests",
        help="Perform concurrent requests to the proxy server",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--proxy-url",
        help="URL of the FlareSolverr proxy server",
        type=str,
    )
    parser.add_argument(
        "--redis-url",
        help="Redis database URL",
        type=str,
    )
    parser.add_argument(
        "--db-url",
        help="Database URL",
        type=str,
    )
    parser.add_argument(
        "--restart-job",
        help="Clear the Redis queue and starts the job from the beginning \
            using the provided --start-url and --language",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--start-url",
        help="The URL to start scraping from",
        type=str,
    )
    parser.add_argument(
        "--language",
        help="The language to filter all requests by",
        type=str,
    )

    return parser


def restart_job():
    """
    This function restarts the crawler job. It deletes the
    associated Redis keys {spider_name}:dupefilter, {spider_name}:requests,
    and sets the {spider_name}::start_urls to the provided start_url.
    """
    redis_url = os.environ["REDIS_URL"]
    spider_name = os.environ["SPIDER_NAME"]
    start_url = os.environ["START_URL"]

    client = redis.Redis.from_url(redis_url)
    with client.pipeline() as pipe:
        pipe.delete(f"{spider_name}:dupefilter")
        pipe.delete(f"{spider_name}:requests")
        pipe.lpush(f"{spider_name}:start_urls", start_url)
        pipe.execute()


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv(find_dotenv())

    # Parse command line arguments
    parser = add_cli_arguments()
    args: Namespace = parser.parse_args()

    # Set spider name
    os.environ["SPIDER_NAME"] = args.spider_name

    # Set or override environment variables
    if args.use_web_cache:
        os.environ["USE_WEB_CACHE"] = str(args.use_web_cache)
    if args.follow_pagination_links:
        os.environ["FOLLOW_PAGINATION_LINKS"] = str(args.follow_pagination_links)
    if args.follow_category_links:
        os.environ["FOLLOW_CATEGORY_LINKS"] = str(args.follow_category_links)
    if args.follow_tag_links:
        os.environ["FOLLOW_TAG_LINKS"] = str(args.follow_tag_links)
    if args.concurrent_proxy_requests:
        os.environ["CONCURRENT_PROXY_REQUESTS"] = str(args.concurrent_proxy_requests)
    if args.proxy_url:
        os.environ["PROXY_URL"] = args.proxy_url
    if args.redis_url:
        os.environ["REDIS_URL"] = args.redis_url
    if args.db_url:
        os.environ["DB_URL"] = args.db_url
    if args.restart_job:
        if args.start_url:
            os.environ["START_URL"] = args.start_url
        else:
            raise ValueError("--start-url is required when --restart-job is provided")
        if args.language:
            os.environ["LANGUAGE"] = args.language
        else:
            raise ValueError(
                "--language is required when --restart-job is provided"
            )
        restart_job()

    # Setup the Spider name
    class NamedSpider(ServersSpider):
        name: str = os.environ["SPIDER_NAME"]

    # Setup the CrawlerProcess
    process = CrawlerProcess(get_project_settings())
    process.crawl(NamedSpider)

    # Start the crawling process
    process.start()
