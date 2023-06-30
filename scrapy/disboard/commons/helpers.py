from disboard.items import DisboardServerItem
from datetime import datetime
from scrapy.http import Response, Request
from typing import Generator


def extract_disboard_server_items(response: Response) -> DisboardServerItem:
    """
    Given a response from a Disboard server list page, yields all
    the DisboardServerItem's from that page.

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
    """
    next_url = response.css(".next a::attr(href)").get()
    if next_url is not None:
        next_url = f"{self.page_iterator_prefix}{response.urljoin(next_url)}{self.language_postfix}"
        yield Request(url=next_url)


def request_all_tag_urls(self, response: Response) -> Generator[Request, None, None]:
    """
    Given a response from a Disboard server list page, returns a generator
    with all the requests for tag pages.

    This function is meant to be used in a scrapy.Spider.parse method.
    """
    tags = response.css(".tag::attr(title)").getall()
    unique_tags_list = list(set(tags))
    for tag in unique_tags_list:
        tag_url = f"{self.base_url}/servers/tag/{tag}{self.language_postfix}"
        yield Request(url=tag_url)


def request_all_category_urls(
    self, response: Response
) -> Generator[Request, None, None]:
    """
    Given a response from a Disboard server list page, returns a generator
    with all the requests for category pages.

    This function is meant to be used in a scrapy.Spider.parse method.
    """
    categories = response.css(".category::attr(href)").getall()
    for category in categories:
        category_url = f"{self.base_url}{response.urljoin(category)}{self.language_postfix}"
        yield Request(url=category_url)
