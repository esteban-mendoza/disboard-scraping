from disboard.items import DisboardServerItem
from datetime import datetime
from scrapy.http import Response, Request
from typing import Generator
from urllib.parse import urljoin


def count_disboard_server_items(response: Response) -> int:
    """
    Given a response from a Disboard server list page, returns the number
    of DisboardServerItem's found in the response.

    If no DisboardServerItem's are found, returns 0.
    """

    server_info_selectorlist = response.css(".server-info")

    return len(server_info_selectorlist)


def extract_disboard_server_items(
    response: Response,
) -> Generator[DisboardServerItem, None, None]:
    """
    Given a response from a Disboard server list page, returns a generator
    of all the DisboardServerItem's from that page.

    If no DisboardServerItem's are found, returns None.

    This function is meant to be used in a scrapy.Spider.parse method.
    """
    server_info_selectorlist = response.css(".server-info")
    server_body_selectorlist = response.css(".server-body")

    response_date = response.headers["Date"].decode()
    scrape_time = datetime.strptime(
        response_date, "%a, %d %b %Y %H:%M:%S %Z"
    ).timestamp()

    for server_info, server_body in zip(
        server_info_selectorlist, server_body_selectorlist
    ):
        platform_link = server_info.css(".server-name a::attr(href)").get()
        guild_id = platform_link.split("/")[-1]
        server_name = server_info.css(".server-name a::text").get().strip()

        server_description = "".join(
            server_body.css(".server-description::text").getall()
        ).strip()

        data_ids = server_body.css(".tag::attr(data-id)").getall()
        tags = server_body.css(".tag::attr(title)").getall()
        tags = [{key: value} for key, value in zip(data_ids, tags)]

        category = server_info.css(".server-category::text").get().strip()
        yield DisboardServerItem(
            scrape_time=scrape_time,
            platform_link=platform_link,
            guild_id=guild_id,
            server_name=server_name,
            server_description=server_description,
            tags=tags,
            category=category,
        )


def request_next_url(self, response: Response) -> Generator[Request, None, None]:
    """
    Given a response from a Disboard server list page, yields a request
    for the next page.

    This function is meant to be used in a scrapy.Spider.parse method.

    The priority of the request is set to 3. Higher priority requests
    are processed earlier.
    """
    next_url = response.css(".next a::attr(href)").get()
    if next_url is not None:
        next_url = f"{self.page_iterator_prefix}{urljoin(self.base_url, next_url)}"
        yield Request(url=next_url, priority=3)


def request_all_category_urls(
    self, response: Response
) -> Generator[Request, None, None]:
    """
    Given a response from a Disboard server list page, returns a generator
    with all the requests for category pages.

    This function is meant to be used in a scrapy.Spider.parse method.

    The priority of the request is set to 2. Higher priority requests
    are processed earlier.
    """
    category_urls = response.css(".category::attr(href)").getall()
    for category_url in category_urls:
        category_url = f"{self.page_iterator_prefix}{self.base_url}{category_url}{self.language_postfix}"
        yield Request(url=category_url, priority=2)


def request_all_tag_urls(self, response: Response) -> Generator[Request, None, None]:
    """
    Given a response from a Disboard server list page, returns a generator
    with all the requests for tag pages.

    This function is meant to be used in a scrapy.Spider.parse method.

    The priority of the request is set to 1. Higher priority requests
    are processed earlier.
    """
    tags = response.css(".tag::attr(title)").getall()
    unique_tags_list = list(set(tags))
    for tag in unique_tags_list:
        tag_url = f"{self.page_iterator_prefix}{self.base_url}/servers/tag/{tag}{self.language_postfix}"
        yield Request(url=tag_url, priority=1)
