from .conftest import spider_mock
from disboard.commons.helpers import (
    count_disboard_server_items,
    has_pagination_links,
    extract_disboard_server_items,
    request_next_url,
    request_all_category_urls,
    request_all_tag_urls,
)
from disboard.items import DisboardServerItem


def test_count_disboard_server_items(sample_response):
    count = count_disboard_server_items(sample_response)
    assert count == 22


def test_has_pagination_links(sample_response):
    has_links = has_pagination_links(sample_response)
    assert has_links


def test_extract_disboard_server_items(sample_response):
    items = list(extract_disboard_server_items(sample_response))
    assert len(items) == 22
    assert isinstance(items[0], DisboardServerItem)
    assert items[0]["server_name"] == "My Hero Academia-Next Generation AU-RP"
    assert items[0]["tags"] == [
        {"39": "anime"},
        {"1236": "my-hero-academia"},
        {"5838": "boku-no-hero-academia"},
        {"6787": "rollenspiel"},
        {"6866": "rollenspiele"},
    ]


def test_request_next_url(spider_mock, sample_response):
    requests = list(request_next_url(spider_mock, sample_response))
    assert len(requests) == 1
    assert requests[0].url == "https://disboard.org/servers/2?fl=de"
    assert requests[0].priority == 22 + 50


def test_request_all_category_urls(spider_mock, sample_response):
    requests = list(request_all_category_urls(spider_mock, sample_response))
    assert len(requests) == 8
    assert requests[0].url == "https://disboard.org/servers/category/gaming?fl=de"
    assert requests[0].priority == 22 + 25


def test_request_all_tag_urls(spider_mock, sample_response):
    requests = list(request_all_tag_urls(spider_mock, sample_response))
    assert len(requests) == 207
    assert requests[0].url == "https://disboard.org/servers/tag/community?fl=de"
    assert requests[0].priority == 22 + 1
    assert requests[1].url == "https://disboard.org/servers/tag/gaming?fl=de"
    assert requests[1].priority == 22 + 1
