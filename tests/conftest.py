import os
import pytest
from scrapy.http import HtmlResponse
from scrapy.settings import Settings


@pytest.fixture
def settings():
    return Settings(
        {
            "USE_WEB_CACHE": False,
            "LANGUAGE": "de",
            "RETRY_HTTP_CODES": [500, 502, 503, 504, 522, 524, 404, 408, 429],
        }
    )


@pytest.fixture
def spider_mock():
    class SpiderMock:
        url_prefix = ""
        language = "de"
        base_url = "https://disboard.org"
        settings = Settings({"USE_WEB_CACHE": False, "LANGUAGE": "de"})

    return SpiderMock()


@pytest.fixture
def blocked_response():
    blocked_site_path = os.path.abspath("tests/sample_files/access_denied.html")
    with open(blocked_site_path, "r") as f:
        html = f.read()
    return HtmlResponse(
        url="https://disboard.org/servers?fl=de",
        headers={"Date": b"Mon, 10 Jul 2023 21:57:03 GMT"},
        body=html,
        encoding="utf-8",
    )


@pytest.fixture
def sample_response():
    example_site_path = os.path.abspath(
        "tests/sample_files/disboard.org_servers_fl=de.html"
    )
    with open(example_site_path, "r") as f:
        html = f.read()
    return HtmlResponse(
        url="https://disboard.org/servers?fl=de",
        headers={"Date": b"Mon, 10 Jul 2023 21:57:03 GMT"},
        body=html,
        encoding="utf-8",
    )
