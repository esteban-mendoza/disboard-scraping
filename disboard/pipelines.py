# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import psycopg
from psycopg.types.json import Jsonb


class DisboardPipeline:
    def process_item(self, item, spider):
        return item


class PostgresPipeline:
    table_name = "public.disboard_servers"

    def __init__(self, db_url):
        self.db_url = db_url

    @classmethod
    def from_crawler(cls, crawler):
        return cls(db_url=crawler.settings.get("DB_URL"))

    def open_spider(self, spider):
        self.client = psycopg.connect(self.db_url)
        self.client.autocommit = True
        self.cursor = self.client.cursor()

    def close_spider(self, spider):
        self.cursor.close()
        self.client.close()

    def process_item(self, item, spider):
        sql = f"""INSERT INTO {self.table_name}
            (scrape_time, platform_link, guild_id, server_name, server_description, tags, category) \
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (guild_id)
            DO UPDATE SET
                scrape_time = EXCLUDED.scrape_time,
                server_name = EXCLUDED.server_name,
                server_description = EXCLUDED.server_description,
                tags = EXCLUDED.tags,
                category = EXCLUDED.category"""
        data = (
            item["scrape_time"],
            item["platform_link"],
            item["guild_id"],
            item["server_name"],
            item["server_description"],
            Jsonb(item["tags"]),
            item["category"],
        )
        self.cursor.execute(sql, data)
        return item
