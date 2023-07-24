from disboard.items import DisboardServerItem
from datetime import datetime
from scrapy.http import Response, Request
from typing import Generator, List
from urllib.parse import urljoin


def blocked_by_cloudflare(response: Response) -> bool:
    """
    Given a response from a Disboard server list page, returns True if
    the response is blocked by Cloudflare, False otherwise.
    """
    title = response.css("title::text").get()
    if title == "Access denied | disboard.org used Cloudflare to restrict access":
        return True
    else:
        return False


def is_server_listing(response: Response) -> bool:
    """
    Given a response from a Disboard server list page, returns True if
    the response is a server listing, False otherwise.
    """
    title = response.css("title::text").get().lower()
    if "discord servers" in title:
        return True
    else:
        return False


def count_disboard_server_items(response: Response) -> int:
    """
    Given a response from a Disboard server list page, returns the number
    of DisboardServerItem's found in the response.

    If no DisboardServerItem's are found, returns 0.
    """
    server_names = response.css(".server-name a::text").getall()

    return len(server_names)


def has_pagination_links(response: Response) -> bool:
    """
    Given a response from a Disboard server list page, returns True if
    the response has pagination links, False otherwise.
    """
    next_url = response.css(".next a::attr(href)").get()

    return next_url is not None


def get_url_postfixes(self) -> List[str]:
    """
    Returns a tuple with the postfixes to append to the URLs of the
    category and tag pages.
    """
    if self.language == "":
        return ["", "?sort=-member_count"]

    language = f"?fl={self.language}"
    language_and_member_count = f"?fl={self.language}&sort=-member_count"
    return [language, language_and_member_count]


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

    response_date = response.headers.get("Date").decode()
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

    The priority of the request is set to the number of servers + 50.
    Higher priority requests are processed earlier.
    """
    n_of_servers = count_disboard_server_items(response)
    next_url = response.css(".next a::attr(href)").get()
    if next_url is not None:
        next_url = f"{self.url_prefix}{urljoin(self.base_url, next_url)}"
        yield Request(url=next_url, priority=n_of_servers + 50)


def request_all_category_urls(
    self, response: Response
) -> Generator[Request, None, None]:
    """
    Given a response from a Disboard server list page, returns a generator
    with all the requests for category pages.

    This function is meant to be used in a scrapy.Spider.parse method.

    The priority of the request is set to the number of servers + 25.
    Higher priority requestsare processed earlier.
    """
    n_of_servers = count_disboard_server_items(response)
    category_urls = response.css(".category::attr(href)").getall()
    postfixes = get_url_postfixes(self)

    for category_url in list(dict.fromkeys(category_urls)):
        for postfix in postfixes:
            url = f"{self.url_prefix}{urljoin(self.base_url, category_url)}{postfix}"
            yield Request(url=url, priority=n_of_servers + 25)


def request_all_tag_urls(self, response: Response) -> Generator[Request, None, None]:
    """
    Given a response from a Disboard server list page, returns a generator
    with all the requests for tag pages.

    This function is meant to be used in a scrapy.Spider.parse method.

    The priority of the request is set to the number of servers + 1.
    Higher priority requests are processed earlier.
    """
    n_of_servers = count_disboard_server_items(response)
    tag_urls = response.css(".tag::attr(href)").getall()
    postfixes = get_url_postfixes(self)

    for tag_url in list(dict.fromkeys(tag_urls)):
        for postfix in postfixes:
            url = f"{self.url_prefix}{urljoin(self.base_url, tag_url)}{postfix}"
            yield Request(url=url, priority=n_of_servers + 1)
