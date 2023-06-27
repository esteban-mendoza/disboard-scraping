# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import psycopg
from itemadapter import ItemAdapter
from psycopg.types.json import Jsonb


class DisboardPipeline:
    def process_item(self, item, spider):
        return item


class PostgresPipeline:
    table_name = "public.disboard_servers"

    def __init__(self, db_host, db_port, db_name, db_user, db_password):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_host=crawler.settings.get("DB_HOST"),
            db_port=crawler.settings.get("DB_PORT"),
            db_name=crawler.settings.get("DB_NAME"),
            db_user=crawler.settings.get("DB_USER"),
            db_password=crawler.settings.get("DB_PASSWORD"),
        )

    def open_spider(self, spider):
        connection_string = f"""
            host={self.db_host} port={self.db_port} dbname={self.db_name} 
            user={self.db_user} password={self.db_password}
        """
        self.client = psycopg.connect(connection_string)
        self.cursor = self.client.cursor()

    def close_spider(self, spider):
        self.client.commit()
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
