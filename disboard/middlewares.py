# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import json
from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.http import HtmlResponse, Request
from logging import getLogger


class FlareSolverrGetSolutionStatusMiddleware:
    """
    This middleware extracts the proper solution status from the "solution"
    given by the FlareSolverr proxy server.

    We are doing this because as for today (2023-07-17), FlareSolverr
    always returns a 200 status code and empty headers.
    See https://github.com/FlareSolverr/FlareSolverr/blob/7728f2ab317ea4b1a9a417b65465e130eb3f337f/src/flaresolverr_service.py#L392
    """

    logger = getLogger(__name__)

    def __init__(self, settings):
        self.retry_http_codes = set(
            int(x) for x in settings.getlist("RETRY_HTTP_CODES")
        )

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_response(self, request, response, spider):
        """
        This method processes the response object and returns a new response
        object with a status code that we can retry, as defined in
        the RETRY_HTTP_CODES setting.
        """

        for status_code in self.retry_http_codes:
            if str(status_code) in response.css("title::text").get():
                self.logger.warning(f"Non 200 response: <{status_code} {response.url}>")
                return response.replace(status=status_code)

        return response


class FlareSolverrProxyMiddleware:
    """
    This middleware uses the FlareSolverr proxy server to bypass Cloudflare's
    anti-bot protection.
    """

    logger = getLogger(__name__)

    def __init__(self, settings):
        self.proxy_url = settings.get("PROXY_URL")
        self.retry_times = settings.getint("RETRY_TIMES")
        self.retry_http_codes = set(
            int(x) for x in settings.getlist("RETRY_HTTP_CODES")
        )

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        return cls(crawler.settings)

    def process_request(self, request, spider):
        """
        This method modifies the request object to use the FlareSolverr
        proxy server.
        """

        # If the request was redirected to FlareSolverr, don't process it again
        if request.meta.get("redirected_to_flare_solverr"):
            return None

        new_request = request.replace(
            url=self.proxy_url,
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    "url": request.url,
                    "cmd": "request.get",
                }
            ).encode("utf-8"),
            meta={
                "original_request": request,
                "dont_redirect": True,
                "dont_filter": True,
                "handle_httpstatus_all": True,
                "redirected_to_flare_solverr": True,
            },
        )
        new_request.meta["download_slot"] = self.proxy_url
        return new_request

    def process_response(self, request, response, spider):
        """
        This method processes the response from the FlareSolverr proxy server.
        If the response is from the proxy server, it will be used to create a
        new HtmlResponse object. Otherwise, the original response will be
        returned.

        If the response from FlareSolverr is not a 200, the request will be
        retried up to retry_times times if the HTTP status code is in the
        retry_http_codes list in the settings.py file.
        """
        # If the request was not redirected to FlareSolverr, return the original response
        if not request.meta.get("redirected_to_flare_solverr"):
            return response

        # If the response from FlareSolverr is not a 200, log a warning
        if response.status != 200:
            self.logger.warning(f"Non 200 response: <{response.status} {response.url}>")

        # If the HTTP status code is in the retry_http_codes list, retry the request
        # up to retry_times times
        original_request = request.meta["original_request"]
        retry_count = original_request.meta.get("flaresolverr_retry_count", 0)

        if response.status in self.retry_http_codes and retry_count < self.retry_times:
            updated_meta = original_request.meta.copy()
            updated_meta.update(
                {
                    "dont_filter": True,
                    "redirected_to_flare_solverr": False,
                    "flaresolverr_retry_count": retry_count + 1,
                }
            )
            original_request = original_request.replace(
                meta=updated_meta, priority=original_request.priority - 10
            )

            self.logger.debug(
                f"Retrying request. Retry count: {retry_count + 1}: <{response.status} {original_request.url}>"
            )
            return original_request

        # If the HTTP status code is not 200 and is not in the retry_http_codes
        # list or the request has been retried retry_times times, log an error
        # and raise an IgnoreRequest exception
        if (
            response.status != 200 and response.status not in self.retry_http_codes
        ) or retry_count >= self.retry_times:
            self.logger.error(
                f"Request failed after {retry_count} retries: <{response.status} {original_request.url}>"
            )
            self.logger.debug(f"Response body: {response.status} {response.body}")
            raise IgnoreRequest(
                f"Request failed after {retry_count} retries: <{response.status} {original_request.url}>"
            )

        try:
            solution_response = json.loads(response.body).get("solution")

        except json.JSONDecodeError:
            self.logger.error(
                f"Failed to parse JSON response: <{response.status} {response.url}>"
            )
            self.logger.debug(f"Response body: {response.body}")
            raise IgnoreRequest(
                f"Failed to parse JSON response: <{response.status} {response.url}>"
            )

        html_response = HtmlResponse(
            url=solution_response.get("url"),
            status=response.status,
            body=solution_response.get("response"),
            headers=response.headers,
            request=original_request,
            protocol=response.protocol,
            encoding="utf-8",
        )
        return html_response
