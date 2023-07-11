import os
import pytest
from scrapy.http import HtmlResponse
from scrapy.settings import Settings


@pytest.fixture
def settings():
    return Settings({"USE_WEB_CACHE": False, "SELECTED_LANGUAGE": ""})


@pytest.fixture
def spider_mock():
    class SpiderMock:
        page_iterator_prefix = ""
        language_postfix = ""
        base_url = "https://disboard.org"
        settings = Settings({"USE_WEB_CACHE": False, "SELECTED_LANGUAGE": ""})

    return SpiderMock()


@pytest.fixture
def sample_response():
    example_site_path = os.path.abspath("tests/sample_files/disboard.org:servers.html")
    with open(example_site_path, "r") as f:
        html = f.read()
    return HtmlResponse(
        url="https://disboard.org/servers",
        headers={"Date": b"Mon, 10 Jul 2023 21:57:03 GMT"},
        body=html,
        encoding="utf-8",
    )
