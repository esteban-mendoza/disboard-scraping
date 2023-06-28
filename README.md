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
Disboard.org](https://disboard.org). To use it, run the following command
in a separate terminal:

```bash
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

The spiders connect to a Postgres database to store the scraped data.
The database connection settings are stored in the `scrapy/disboard/settings.py`
file under the `## Database connection` section.

For a minimal local run, use the command below.

```bash
cd scrapy
scrapy crawl servers
```

The flag `-o servers.jsonl` will append the output to a JSON Lines file.

## Configuration

The `scrapy/disboard/settings.py` file contains the settings for the project.
The following custom settings have been added:

- `FLARE_SOLVERR_URL`: The URL of the FlareSolverr proxy server. By default,
- it is set to `http://localhost:8191/v1`. In order for the FlareSolverr to be
- used, the following lines must be uncommented in `settings.py`:

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
- `FOLLOW_TAG_LINKS`: If set to `True`, the spiders will follow the tag
  links on a given server listing. Be aware that this will **hugely** increase
  the amount of scheduled requests.
- `FOLLOW_CATEGORY_LINKS`: If set to `True`, the spiders will follow the
  category links on a given server listing.
- `FILTER_BY_LANGUAGE`: If set to `True`, the spiders will request the server
  listing for each language and filter the results by the language of the server.

## Database connection

The project can be configured to store the scraped data in a database.
It currently supports a connection to a Postgres database. In order to use it,
make sure that the `settings.py` file contains the following lines:

```python
ITEM_PIPELINES = {
    "disboard.pipelines.PostgresPipeline": 300,
}
```

The database connection settings are stored in the `scrapy/disboard/settings.py`
file under the `## Database connection` section.
