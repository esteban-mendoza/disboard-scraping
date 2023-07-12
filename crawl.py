"""
This is the main entry point of the application.

The application is a Scrapy spider that crawls Disboard.org
and extracts information about Discord servers.

This file is a utility script that allows the user to run the spider
from the command line and override the default settings.

The default settings are stored in an .env file. The user can override
the default settings by passing command line arguments.
"""
import multiprocessing
import os
import redis
import time

from argparse import ArgumentParser, Namespace
from dotenv import load_dotenv, find_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from disboard.spiders.servers import ServersSpider


def add_cli_arguments() -> Namespace:
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
    parser.add_argument(
        "--log-file",
        help="The file to write logs to",
        type=str,
        default="scrapy.log",
    )
    parser.add_argument(
        "--proxy-url",
        help="URL of the FlareSolverr proxy server",
        type=str,
    )
    parser.add_argument(
        "--proxy-pool",
        help="Path to the proxy pool file",
        type=str,
    )

    return parser.parse_args()


def setup_environment(args: Namespace) -> None:
    """
    Setup environment variables based on command line arguments.
    """
    os.environ["SPIDER_NAME"] = args.spider_name

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


def restart_job() -> None:
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

    client.close()


def run_spider_with_proxy(proxy_url: str) -> None:
    """
    Runs a single spider with the given proxy url.
    """
    os.environ["PROXY_URL"] = proxy_url

    class NamedSpider(ServersSpider):
        name = os.environ["SPIDER_NAME"]

    process = CrawlerProcess(get_project_settings())
    process.crawl(NamedSpider)
    process.start()


def run_spiders(args: Namespace) -> None:
    """
    Run multiple spiders in parallel using different proxies.
    """
    processes = []
    try:
        if args.restart_job:
            restart_job()

        with open("proxies.txt", "r") as f:
            proxy_urls = [line.strip() for line in f]

        for i, proxy_url in enumerate(proxy_urls):
            process = multiprocessing.Process(
                target=run_spider_with_proxy, args=(proxy_url,)
            )
            process.start()
            if i == 0:
                time.sleep(60)
            processes.append(process)

        for process in processes:
            process.join()

    except KeyboardInterrupt:
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv(find_dotenv())

    # Parse command line arguments
    args = add_cli_arguments()
    setup_environment(args)

    # Start the crawling processes
    run_spiders(args)
