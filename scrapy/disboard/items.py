# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from typing import Dict, List
import scrapy


class DisboardServerItem(scrapy.Item):
    """
    This item represents a server scraped from Disboard.

    Attributes:
        scrape_time (float): Timestamp of the response when the item was scraped.
        platform_link (str): The URL of the server on Disboard.
        guild_id (str): The Discord guild ID of the server.
        server_name (str): The name of the server.
        server_description (str): The description of the server.
        tags (List[Dict[str, str]]): A list of dictionaries associating each
            data-id (a Disboard's internal key for enumerating tags) to its
            corresponding tag name.
    """

    scrape_time: float = scrapy.Field()
    platform_link: str = scrapy.Field()
    guild_id: str = scrapy.Field()
    server_name: str = scrapy.Field()
    server_description: str = scrapy.Field()
    tags: List[Dict[str, str]] = scrapy.Field()
    category: str = scrapy.Field()
