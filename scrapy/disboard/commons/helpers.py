from disboard.items import DisboardServerItem
from scrapy.http import Response, Request
from datetime import datetime


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


def request_next_url(self, response: Response) -> Request:
    """
    Given a response from a Disboard server list page, requests the next page.

    This function is meant to be used in a scrapy.Spider.parse method.
    """
    next_url = response.css(".next a::attr(href)").get()
    if next_url is not None:
        next_url = f"{self.page_iterator_prefix}{response.urljoin(next_url)}"
        yield Request(
            url=next_url,
            meta={**self.default_request_args, "errback": self.error_handler},
        )


def request_all_tag_urls(self, response: Response) -> Request:
    """
    Given a response from a Disboard server list page, requests all tag pages.

    This function is meant to be used in a scrapy.Spider.parse method.
    """
    tags = response.css(".tag::attr(title)").getall()
    for tag in tags:
        tag_url = f"{self.base_url}/servers/tag/{tag}"
        yield Request(
            url=tag_url,
            meta={**self.default_request_args, "errback": self.error_handler},
        )
