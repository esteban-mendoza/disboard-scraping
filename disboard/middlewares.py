# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import json
from scrapy import signals
from scrapy.http import HtmlResponse, Response
from logging import getLogger, INFO, WARNING
from twisted.internet.threads import deferToThread


class FlareSolverrProxyMiddleware:
    """
    This middleware uses the FlareSolverr proxy server to bypass Cloudflare's
    anti-bot protection.
    """

    logger = getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        """
        This method modifies the request object to use the FlareSolverr
        proxy server.
        """

        # If the request is already processed by FlareSolverr, don't process it again
        if request.meta.get("processed_by_flare_solverr"):
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
                "handle_httpstatus_all": True,
                "processed_by_flare_solverr": True,
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
        """
        processed_by_flare_solverr = request.meta.get("processed_by_flare_solverr")
        if processed_by_flare_solverr:
            original_request = request.meta["original_request"]
            solution_response = json.loads(response.body).get("solution")
            html_response = HtmlResponse(
                url=solution_response.get("url"),
                body=solution_response.get("response"),
                headers=response.headers,
                request=original_request,
                protocol=response.protocol,
                encoding="utf-8",
            )
            self.logger.log(
                INFO,
                f"Successfully got response from proxy server {self.proxy_url}: <{html_response.status} {html_response.url}>",
            )
            return html_response
        else:
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
        spider.logger.info("Spider opened: %s" % spider.name)
