# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
import psycopg


class DisboardPipeline:
    def process_item(self, item, spider):
        return item


class PostgresPipeline:
    table_name = "disboard_servers"

    def __init__(self, db_uri):
        self.db_uri = db_uri

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("DB_URI"),
        )

    def open_spider(self, spider):
        self.client = psycopg.connect(self.db_uri)
        self.cursor = self.client.cursor()

    def close_spider(self, spider):
        self.client.commit()
        self.cursor.close()
        self.client.close()

    def process_item(self, item, spider):
        sql = (
            f"INSERT INTO {self.table_name} (scrape_time, platform_link, guild_id, discord_invite_code, server_name, server_description, tags, category) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        )
        data = {
            "scrape_time": item["scrape_time"],
            "platform_link": item["platform_link"],
            "guild_id": item["guild_id"],
            "discord_invite_code": item["discord_invite_code"],
            "server_name": item["server_name"],
            "server_description": item["server_description"],
            "tags": json.dumps(item["tags"]),
            "category": item["category"],
        }
        self.cursor.execute(sql, data)
        return item
