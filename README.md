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
The database connection settings are stored in the `disboard/settings.py`
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
python3 crawl.py --spider-name servers --restart-job --language ''
```

You can run the following command to see all the available options to
configure the crawler via the command line.

```bash
python3 crawl.py --help
```

## Configuration

The `disboard/settings.py` file contains the settings for the project.
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
- `LANGUAGE`: The language code that will be appended to all URLs.
  By default, it is set to `""` ––an empty string––. This means that the spiders
  won't append any language code to the URLs. If you want to scrape the website
  in a specific language, you can set this variable to the corresponding
  language code. `disboard/commons/constants.py` contains a list of all the
  available language codes.
- `PROXY_URL`: The URL of the FlareSolverr proxy server.
- `REDIS_URL`: The URL of the Redis server. The spiders use Redis to queue
  and filter out duplicate requests.
- `DB_URL`: The URL of the Postgres database. The spiders use the database
  to store the scraped data. For more information, see the
  [Database connection](#database-connection) section below.

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
variables to be set in a `.env` file in the root directory.
This is also true for the Redis connection and the FlareSolverr proxy server.

## Custom downloader middlewares

The project uses the following custom downloader middlewares:

- `disboard.middlewares.FlareSolverrRedirectMiddleware`: This middleware
  redirects the requests to a [FlareSolverr proxy server](https://github.com/FlareSolverr/FlareSolverr)
  and extracts the solution response from the proxy server's response.
- `disboard.middlewares.FlareSolverrRetryMiddleware`: This middleware
  retries the requests that failed due to the FlareSolverr proxy server.
- `disboard.middlewares.FlareSolverrGetSolutionStatusMiddleware`:
  This middleware extracts the correct status from the Disboard website's
  response. We are doing this because as for today (2023-07-24) the
  FlareSolverr proxy server always returns a `200` status and empty headers.
  
  For more details, refer to [FlareSolverr's source code](https://github.com/FlareSolverr/FlareSolverr/blob/7728f2ab317ea4b1a9a417b65465e130eb3f337f/src/flaresolverr_service.py#L392).

In order to use FlareSolverr, the `settings.py` file must contain the following lines:

```python
DOWNLOADER_MIDDLEWARES = {
    "disboard.middlewares.FlareSolverrRedirectMiddleware": 542,
}
```

For more information about this, see [_Activating a Downloader Middleware_](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#activating-a-downloader-middleware).

For more information about downloader middlewares, see
[Scrapy's documentation on Downloader Middlewares](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html).

## Custom item pipelines

The project uses the following custom item pipelines:

- `disboard.pipelines.PostgresPipeline`: This pipeline stores the scraped data
  in a Postgres database. For more information, see the
  [Database connection](#database-connection) section above.
- `diwboard.pipelines.ServersGuildIdPipeline`: This pipeline stores
  the unique `guild_id`'s of the scraped servers in a Redis set for keeping
  track of the servers that have already been scraped.
  
  When a spider finishes its execution it will report two counters:
  `item_scraped_count/new` and `item_scraped_count/old` that will
  indicate the number of scraped servers that were not in the Redis set
  associated with the job and the number of scraped servers that were
  already in the Redis set associated with the job, respectively.

In order to activate or deactivate a pipeline, the `ITEM_PIPELINES`
variable msut be set in the `settings.py` file. For more information,
see [_Activating an Item Pipeline Component_](https://docs.scrapy.org/en/latest/topics/item-pipeline.html#activating-an-item-pipeline-component).

For more information about item pipelines, see
[Srapy's documentation on Item Pipelines](https://docs.scrapy.org/en/latest/topics/item-pipeline.html).
