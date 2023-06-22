from disboard.items import DisboardServerItem
from scrapy.http import Response
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
