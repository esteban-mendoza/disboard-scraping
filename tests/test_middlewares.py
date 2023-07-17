import pytest
from scrapy.http import HtmlResponse
from disboard.middlewares import FlareSolverrGetSolutionStatusMiddleware


class TestFlareSolverrGetSolutionStatusMiddleware:
    @pytest.fixture
    def middleware(self, settings):
        return FlareSolverrGetSolutionStatusMiddleware(settings)

    @pytest.mark.parametrize(
        "retry_code", [500, 502, 503, 504, 522, 524, 404, 408, 429]
    )
    def test_process_response_retries(self, middleware, spider_mock, retry_code):
        html = f"<html><head><title>{retry_code} Error</title></head></html>"
        response = HtmlResponse(
            status=200,
            url="http://test.com",
            body=html,
            request=None,
            encoding="utf-8",
        )
        response = middleware.process_response(None, response, spider_mock)

        assert response.status == retry_code

    def test_process_response_returns_original_response(self, middleware, spider_mock):
        response = HtmlResponse(
            status=200,
            url="http://test.com",
            body="<html><head><title>Example title</title></head></html>",
            request=None,
            encoding="utf-8",
        )
        response = middleware.process_response(None, response, spider_mock)

        assert response.status == 200
