# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import requests
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.exceptions import IgnoreRequest
from disboard.settings import FLARE_SOLVERR_URL
from logging import getLogger, INFO

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class DisboardSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class FlareSolverrDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    logger = getLogger(__name__)
    proxy_url = FLARE_SOLVERR_URL

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        """
        This method forwards all requests to the FlareSolverr server,
        awaits and returns the response from the proxy server.
        """

        post_body = {
            "url": request.url,
            "cmd": "request.get",
            "maxTimeout": 60000,
        }

        response = requests.post(
            self.proxy_url, headers={"Content-Type": "application/json"}, json=post_body
        )

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
                f"Successfully got response from proxy server: <{html_response.status} {html_response.url}>",
            )
            return html_response
        else:
            self.logger.log(
                INFO,
                f"Failed to get response from proxy server: <{response.status_code} {response.reason}>",
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
        spider.logger.info("Spider opened: %s" % spider.name)