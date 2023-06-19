# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ServerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    scrape_time = scrapy.Field()
    platform_link = scrapy.Field()
    guild_id = scrapy.Field()
    discord_invite_code = scrapy.Field()
    server_name = scrapy.Field()
    server_description = scrapy.Field()
    tags = scrapy.Field()
    category = scrapy.Field()
