# Disboard Scraper

## Installation

The current version of the project is tested with Python 3.8.12.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

## Usage

In its current state, the project uses the [FlareSolverr proxy server](https://github.com/FlareSolverr/FlareSolverr)
to bypass Cloudflare's anti-bot protection and be able to connect to [Disboard.org](https://disboard.org). To use it, 
run the following command in a separate terminal:

```bash
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

For a minimal local run, use the command below. The flag `-o servers.jsonl` will append the output to a JSON Lines file.

```bash
cd scrapy
scrapy crawl servers -o servers.jsonl
```

## Configuration

The `scrapy/disboard/settings.py` file contains the settings for the project. The following custom settings have been added:

- `USE_WEB_CACHE`: If set to `True`, the project will use the [Web Cache](https://webcache.googleusercontent.com/) to scrape the website. This is useful if you want to scrape the website without using a proxy server.
- `FOLLOW_PAGINATION_LINKS`: If set to `True`, the project will follow the pagination links on a given server listing.
- `FOLLOW_TAG_LINKS`: If set to `True`, the project will follow the tag links on a given server listing. Be aware that this will **hugely** increase the number of requests made to the website.
- `FLARE_SOLVERR_URL`: The URL of the FlareSolverr proxy server. By default, it is set to `http://localhost:8191/v1`.
