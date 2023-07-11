# Disboard Scraper

## Installation

The current version of the project is tested with Python 3.8.12.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

In its current state, the project uses the [FlareSolverr proxy server](https://github.com/FlareSolverr/FlareSolverr)
to bypass Cloudflare's anti-bot protection and be able to connect to [
Disboard.org](https://disboard.org). To use it locally, run the following
command in a separate terminal:

```bash
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

A Redis server is required for queuing and filtering out duplicate requests.
To use it locally, run the following command in a separate terminal:

```bash
docker run -d --name redis -p 6379:6379 redis
```

The spiders connect to a Postgres database to store the scraped data.
The database connection settings are stored in the `scrapy/disboard/settings.py`
file under the `## Database connection` section. For more information, see
the [Database connection](#database-connection) section below.

For a minimal local run, make sure that the following environment variables
are set in a `.env` file in the root directory. For more information, see
the [Configuration](#configuration) section below.

- `PROXY_URL`: The URL of the FlareSolverr proxy server.
- `REDIS_URL`: The URL of the Redis server.
- `DB_URL`: The URL of the Postgres database.

You can run the following command to start crawling the website. It will start
a crawling job with the default settings from the beginning ––without resuming
from the last saved state––. It will start crawling from `https://disboard.org/servers`
and will scrape the website without filtering out by language.

```bash
python3 crawl.py --spider servers --restart-job --start-url 'https://disboard.org/servers' --selected-language ''
```

You can run the following command to see all the available options to
configure the crawler via the command line.

```bash
python3 crawl.py --help
```

## Configuration

The `scrapy/disboard/settings.py` file contains the settings for the project.
Each of the settings can be overridden by setting the corresponding environment
variable in a `.env` file in the root directory.

The following settings are available:

- `USE_WEB_CACHE`: Default: `False`. If set to `True`, the spiders will use
  [Google's Web Cache](https://webcache.googleusercontent.com/)
  to scrape the website. This is useful if you want to scrape the website
  without using a proxy server or for testing purposes.
  Note that if you are using Google's Web Cache, you should probably
  disable the `FlareSolverrDownloaderMiddleware` in `settings.py`.
- `FOLLOW_PAGINATION_LINKS`: Default: `True`. If set to `True`, the spiders
  will follow the pagination links on a given server listing.
- `FOLLOW_CATEGORY_LINKS`: Default: `True`. If set to `True`, the spiders
  will follow the category links on a given server listing.
- `FOLLOW_TAG_LINKS`: Default: `True`. If set to `True`, the spiders will
  follow the tag links on a given server listing. Be aware that this will **hugely** increase the amount of scheduled requests.
- `SELECTED_LANGUAGE`: The language code that will be appended to all URLs.
  By default, it is set to `""` ––an empty string––. This means that the spiders
  won't append any language code to the URLs. If you want to scrape the website
  in a specific language, you can set this variable to the corresponding
  language code. `disboard/commons/constants.py` contains a list of all the
  available language codes.
- `PROXY_URL`: The URL of the FlareSolverr proxy server. In order to use
  FlareSolverr, the `settings.py` file must contain the following lines:

  ```python
  DOWNLOADER_MIDDLEWARES = {
      "disboard.middlewares.FlareSolverrDownloaderMiddleware": 543,
  }
  ```

- `CONCURRENT_PROXY_REQUESTS`: Default: `False`. If `True` and
  `PROXY_URL` is set, the spiders will perform concurrent requests to the
  proxy server. This will speed up the crawling process, but it will also
  increase the load on the proxy server.
- `REDIS_URL`: The URL of the Redis server. The spiders use Redis to queue
  and filter out duplicate requests.
- `DB_URL`: The URL of the Postgres database. The spiders use the database
  to store the scraped data. For more information, see the
  [Database connection](#database-connection) section below.
- `LOG_FILE`: The path to the log file. By default, it is set to
  `scrapy.log` in the root directory.

## Database connection

The project can be configured to store the scraped data in a database.
It currently supports a connection to a Postgres database. In order to use it,
make sure that the `settings.py` file contains the following lines:

```python
ITEM_PIPELINES = {
    "disboard.pipelines.PostgresPipeline": 300,
}
```

The database connection settings are configured in the `scrapy/disboard/settings.py`
file under the `## Database connection` section. The connection requires variables
to be set in a `.env` file in the root directory.
This is also true for the Redis connection and the FlareSolverr proxy server.
