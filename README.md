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

For a minimal local run, use the command below.

```bash
scrapy crawl servers
```

## Configuration

The `scrapy/disboard/settings.py` file contains the settings for the project.
The following custom settings have been added:

- `START_FROM_BEGINNING`: If set to `True`, the spiders will delete the
  Redis keys and start scraping from the beginning. If set to `False`, the
  spiders will continue scraping from where they left off.

  **Note:** This setting is still in development. In order to start scraping
  from the beginning, you will have to manually delete the Redis keys and
  push the starting URLs to the Redis queue.

  To delete the Redis keys, connect to the Redis server with
  `redis-cli` and run the following:

  ```bash
  redis-cli
  del servers:dupefilter
  del servers:requests
  lpush servers:requests https://disboard.org/servers
  ```

- `FILTER_BY_LANGUAGE`: If True, the crawler will append `SELECTED_LANGUAGE`
  language code to all URLs. This is useful if you want to scrape the website
  for a specific language.
- `SELECTED_LANGUAGE`: The language code that will be appended to all URLs.
  `FILTER_BY_LANGUAGE` must be set to `True` for this to work.

- `FLARE_SOLVERR_URL`: The URL of the FlareSolverr proxy server. By default,
  it is set to `http://localhost:8191/v1`. In order to use the FlareSolverr,
  the `settings.py` file must contain the following lines:

  ```python
  DOWNLOADER_MIDDLEWARES = {
      "disboard.middlewares.FlareSolverrDownloaderMiddleware": 543,
  }
  ```

- `USE_WEB_CACHE`: If set to `True`, the spiders will use [Google's Web Cache](https://webcache.googleusercontent.com/)
  to scrape the website. This is useful if you want to scrape the website
  without using a proxy server. Note that if you are using Google's Web Cache,
  you should probably disable the `FlareSolverrDownloaderMiddleware`
  in `settings.py`.
- `FOLLOW_PAGINATION_LINKS`: If set to `True`, the spiders will follow
  the pagination links on a given server listing.
- `FOLLOW_CATEGORY_LINKS`: If set to `True`, the spiders will follow the
  category links on a given server listing.
- `FOLLOW_TAG_LINKS`: If set to `True`, the spiders will follow the tag
  links on a given server listing. Be aware that this will **hugely** increase
  the amount of scheduled requests.

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
file under the `## Database connection` section. The connection requires
certain environment variables to be set in a `.env` file in the root directory.
This is also true for the Redis connection and the FlareSolverr proxy server.
