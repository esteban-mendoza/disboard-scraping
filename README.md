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

For a minimal local run, use the command below. The flag `-o servers.jsonl` will append the output to a JSON Lines file.

```bash
cd disboard
scrapy crawl servers -o servers.jsonl
```
