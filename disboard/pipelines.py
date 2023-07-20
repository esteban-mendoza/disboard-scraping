# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import redis
import psycopg
from psycopg.types.json import Jsonb


class ServersGuildIdPipeline:
    """
    This pipeline is used to keep track of the guild_ids that have been scraped
    in the current run. This is used to determine which guild_ids are new and
    which guild_ids are old.
    """

    set_name = "guild_id"

    def __init__(self, spider_name, redis_url, stats):
        self.key_name = f"{spider_name}:{self.set_name}"
        self.redis_url = redis_url
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        spider_name = crawler.spider.name
        redis_url = crawler.settings.get("REDIS_URL")
        stats = crawler.stats
        return cls(spider_name=spider_name, redis_url=redis_url, stats=stats)

    def open_spider(self, spider):
        self.client = redis.Redis.from_url(self.redis_url)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        guild_id = item["guild_id"]
        if self.client.sismember(self.key_name, guild_id):
            self.stats.inc_value("item_scraped_count/old")
        else:
            self.stats.inc_value("item_scraped_count/new")
            self.client.sadd(self.key_name, guild_id)

        return item


class PostgresPipeline:
    """
    This pipeline is used to store the scraped data in a Postgres database.
    """

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
