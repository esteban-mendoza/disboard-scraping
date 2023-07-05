# Scrapy settings for disboard project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "disboard"

SPIDER_MODULES = ["disboard.spiders"]
NEWSPIDER_MODULE = "disboard.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "disboard (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 2

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 6
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 1
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "disboard.middlewares.DisboardSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "disboard.middlewares.FlareSolverrDownloaderMiddleware": 543,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "disboard.pipelines.PostgresPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 6
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.2
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True

# Enable and configure retry middleware
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#module-scrapy.downloadermiddlewares.retry
RETRY_ENABLED = True
# Maximum number of times to retry, in addition to the first download.
RETRY_TIMES = 1
# Which HTTP response codes to retry.
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 404, 408, 429]


# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Logging settings
# See https://docs.scrapy.org/en/latest/topics/logging.html#logging-settings
# File name to use for logging output. If None, standard error will be used.
LOG_FILE = "disboard.log"
# If LOG_FILE_APPEND = False, the log file specified with LOG_FILE will be overwritten
LOG_FILE_APPEND = True
# The encoding to be used for logging
LOG_ENCODING = "utf-8"
# If LOG_STDOUT = True, all standard output (and error) of the process will be redirected to the log.
LOG_STDOUT = True

# Configure breadth-first crawling
# See https://docs.scrapy.org/en/latest/faq.html#does-scrapy-crawl-in-breadth-first-or-depth-first-order
# DEPTH_PRIORITY = 1
# SCHEDULER_DISK_QUEUE = "scrapy.squeues.PickleFifoDiskQueue"
# SCHEDULER_MEMORY_QUEUE = "scrapy.squeues.FifoMemoryQueue"

# Custom settings
# Sensible settings are stored in a .env local file in the project directory
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# If True, the crawler will delete all data from dupefilter and scheduler
# and start from the start_url
# TODO: Implement this functionality
START_FROM_BEGINNING = True
# If True, the crawler will use Google's web cache to get the HTML of the page
USE_WEB_CACHE = False
# If True, the crawler will follow pagination links
FOLLOW_PAGINATION_LINKS = True
# If True, the crawler will follow category links
FOLLOW_CATEGORY_LINKS = True
# If True, the crawler will follow tag links
FOLLOW_TAG_LINKS = True
# If True, the crawler will append SELECTED_LANGUAGE language code to all URLs
FILTER_BY_LANGUAGE = True
# The language to filter all requests
SELECTED_LANGUAGE = "en"
# URL of the FlareSolverr proxy server
FLARE_SOLVERR_URL = os.getenv("FLARE_SOLVERR_URL")

# Scrapy-Redis settings
# See https://github.com/rmax/scrapy-redis/wiki/Usage
# Enables scheduling storing requests queue in redis
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# Ensure all spiders share same duplicates filter through redis
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# Scheduler queue class:
# - Use LifoQueue to process requests in Depth-first order
# - Use FifoQueue to process requests in Breadth-first order
# - Use PriorityQueue to process requests by priority
SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.PriorityQueue"
# Don't cleanup Redis queues. Allows to pause/resume crawls.
SCHEDULER_PERSIST = True

# Database settings
# Redis database environment variables
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

# Postgres environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
