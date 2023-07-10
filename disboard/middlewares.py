# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import requests
from scrapy import signals
from scrapy.http import HtmlResponse
from logging import getLogger, INFO, WARNING
from twisted.internet.threads import deferToThread


class FlareSolverrProxyMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    logger = getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        """
        This method forwards all requests to the FlareSolverr server.
        It awaits and returns the response from the proxy server.

        If CONCURRENT_PROXY_REQUESTS is set to True, the request is
        processed in a concurrent thread. Otherwise, the request
        blocks the main thread and is processed synchronously.
        """
        if self.concurrent_proxy_requests:
            return deferToThread(self._process_request, request, spider)
        else:
            return self._process_request(request, spider)

    def _process_request(self, request, spider):
        """
        This method is called in a concurrent thread. It sends a POST
        request to the FlareSolverr server and processes the response
        to return a Scrapy Response object.
        """
        post_body = {
            "url": request.url,
            "cmd": "request.get",
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(self.proxy_url, headers=headers, json=post_body)

        if response.status_code == 200:
            solution_response = response.json()["solution"]
            html_response = HtmlResponse(
                url=solution_response["url"],
                body=solution_response["response"],
                headers=response.headers,
                request=request,
                protocol=response.raw.version,
                encoding="utf-8",
            )
            self.logger.log(
                INFO,
                f"Successfully got response from proxy server {self.proxy_url}: <{html_response.status} {html_response.url}>",
            )
            return html_response
        else:
            self.logger.log(
                WARNING,
                f"Proxy server {self.proxy_url}. URL response {request.url}: <{response.status_code} {response.reason}>",
            )

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        self.proxy_url = spider.settings.get("PROXY_URL")
        self.concurrent_proxy_requests = spider.settings.get(
            "CONCURRENT_PROXY_REQUESTS"
        )
        spider.logger.info("Spider opened: %s" % spider.name)
