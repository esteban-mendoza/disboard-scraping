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
import sys
import redis
import time

from datetime import datetime
from argparse import ArgumentParser, Namespace
from disboard.commons.constants import DISBOARD_URL, WEBCACHE_URL
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
        "-n",
        "--spider-name",
        help="The name of the spider. Note that this name will also be \
            used as the Redis' keys for queueing and filtering requests.\n\
            This name allows you to run multiple spiders with different settings \
            at the same time.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-l",
        "--language",
        help="The language to filter all requests by",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-w",
        "--use-web-cache",
        help="Use Google's web cache to get the HTML of the page",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-npl",
        "--dont-follow-pagination-links",
        help="Deactivate following pagination links (the default behavior)",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-ncl",
        "--dont-follow-category-links",
        help="Deactivate following category links (the default behavior)",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-ntl",
        "--dont-follow-tag-links",
        help="Deactivate following tag links (the default behavior)",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-redis",
        "--redis-url",
        help="Redis database URL",
        type=str,
    )
    parser.add_argument(
        "-db",
        "--db-url",
        help="Database URL",
        type=str,
    )
    parser.add_argument(
        "-r",
        "--restart-job",
        help="Clear the Redis queue and starts the job from the beginning \
            using the provided --start-url and --language",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-url",
        "--start-url",
        help="The URL to start scraping from",
        type=str,
    )
    parser.add_argument(
        "-proxy",
        "--proxy-url",
        help="URL of the FlareSolverr proxy server",
        type=str,
    )

    return parser.parse_args()


def setup_environment(args: Namespace) -> None:
    """
    Setup environment variables based on command line arguments.
    """
    os.environ["SPIDER_NAME"] = args.spider_name
    os.environ["LANGUAGE"] = args.language

    os.environ["USE_WEB_CACHE"] = str(args.use_web_cache)
    os.environ["FOLLOW_PAGINATION_LINKS"] = str(not args.dont_follow_pagination_links)
    os.environ["FOLLOW_CATEGORY_LINKS"] = str(not args.dont_follow_category_links)
    os.environ["FOLLOW_TAG_LINKS"] = str(not args.dont_follow_tag_links)
    if args.proxy_url:
        os.environ["PROXY_URL"] = args.proxy_url
    if args.redis_url:
        os.environ["REDIS_URL"] = args.redis_url
    if args.db_url:
        os.environ["DB_URL"] = args.db_url
    if args.restart_job:
        os.environ["RESTART_JOB"] = str(args.restart_job)


def get_start_urls() -> list:
    """
    This function returns a list of start_urls based on the
    selected language.
    """
    prefix = WEBCACHE_URL if os.getenv("USE_WEB_CACHE", False) else ""

    language = os.environ["LANGUAGE"]
    base_url = DISBOARD_URL

    by_language = f"{prefix}{base_url}?fl={language}"
    by_language_and_members = f"{prefix}{base_url}?fl={language}&sort=member_count"
    return [
        by_language,
        by_language_and_members,
    ]


def restart_job() -> None:
    """
    This function restarts the crawler job. It deletes the
    associated Redis keys {spider_name}:dupefilter, {spider_name}:requests,
    and sets the {spider_name}::start_urls to the necessary start_urls.
    """
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


def is_requests_queue_empty() -> bool:
    """
    This function checks if the requests queue is empty.
    """
    redis_url = os.environ["REDIS_URL"]
    spider_name = os.environ["SPIDER_NAME"]

    client = redis.Redis.from_url(redis_url)
    requests_queue_length = client.zcard(f"{spider_name}:requests")

    client.close()
    return requests_queue_length == 0


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


def run_spiders() -> list:
    """
    Run multiple spiders in parallel using different proxies.
    """
    processes = []

    try:
        with open("proxies.txt", "r") as f:
            proxy_urls = [line.strip() for line in f]

        for i, proxy_url in enumerate(proxy_urls):
            process = multiprocessing.Process(
                target=run_spider_with_proxy, args=(proxy_url,)
            )
            process.start()
            processes.append(process)
            if i == 0:
                wait_time = 40
                print(
                    f"[{datetime.now()}] Waiting {wait_time} seconds for the first spider..."
                )
                time.sleep(wait_time)

        return processes
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
        sys.exit(0)


def run_scheduled_spiders(execution_time: float, wait_time: float) -> None:
    """
    This function will run the spiders during the execution_time (in seconds),
    wait for wait_time (in seconds), and then repeat the process.

    If the environment variable RESTART_JOB is set to True, the job will be
    restarted before running the spiders.
    """
    try:
        if os.getenv("RESTART_JOB", False):
            print(f"[{datetime.now()}] Restarting job...")
            restart_job()
            os.environ["RESTART_JOB"] = "False"

        while True:
            processes = run_spiders()
            print(f"[{datetime.now()}] Running {len(processes)} spiders...")

            print(f"[{datetime.now()}] Waiting {execution_time} seconds...")
            time.sleep(execution_time)

            print(f"[{datetime.now()}] Terminating spiders...")
            for process in processes:
                process.terminate()

            if is_requests_queue_empty():
                print(f"[{datetime.now()}] Requests queue is empty. Exiting...")
                sys.exit(0)

            print(
                f"[{datetime.now()}] Spider execution finished. Waiting {wait_time} seconds..."
            )
            time.sleep(wait_time)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv(find_dotenv())
    print(f"[{datetime.now()}] Loaded environment variables from .env file")

    # Parse command line arguments
    args = add_cli_arguments()
    setup_environment(args)
    print(f"[{datetime.now()}] Parsed command line arguments")

    # Start the crawling processes
    print(f"[{datetime.now()}] Starting crawling processes...")
    run_scheduled_spiders(60 * 60 * 1.5, 60 * 15)
