# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import datetime
import json
import logging
import requests
import random

from JFB.utils import localtime_to_datetime
from JFB.utils import get_now_datetime

from scrapy import signals
from templateSpider.common.conf import proxy_ip_url
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from templateSpider.settings import proxy_pool
from templateSpider.settings import proxy_num
from templateSpider.settings import last_proxy

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from twisted.internet import defer
from twisted.internet.error import (
    ConnectError,
    ConnectionDone,
    ConnectionLost,
    ConnectionRefusedError,
    DNSLookupError,
    TCPTimedOutError,
    TimeoutError,
)
from twisted.web.client import ResponseFailed

from scrapy.exceptions import NotConfigured
from scrapy.utils.response import response_status_message
from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.utils.python import global_object_name

logger = logging.getLogger(__name__)

__author__ = 'jiangfb'

class MyProxyMiddleware:

    @staticmethod
    def is_expire(proxy_json):
        expire_time_str = proxy_json["data"]["expire_time"]
        expire_time = localtime_to_datetime(expire_time_str)
        now_time = get_now_datetime()
        if expire_time < now_time:
            return True
        return False

    def remove_proxy(self, ip_port, proxy_json):
        res = requests.get(url=proxy_ip_url, data=json.dumps(proxy_json, ensure_ascii=False).encode("utf-8"), timeout=20)
        logger.info(f"delete a ip_port from online: {ip_port}")
        ip_port = self.fill_proxy(res)
        return ip_port

    @staticmethod
    def fill_proxy(res):
        """填充ip池，记录last_proxy"""
        proxy_json = res.json()
        data = proxy_json["data"]
        ip_port = data["ip"] + ":" + str(data["port"])
        proxy_pool[ip_port] = proxy_json
        last_proxy["ip_port"] = ip_port
        last_proxy["proxy_json"] = proxy_json
        logger.info(f"fill in a proxy: {ip_port}, current number of proxies: {len(proxy_pool)}")
        return ip_port

    @staticmethod
    def is_pool_num():
        """判断pool是否大于proxy_num个"""
        num = len(proxy_pool)
        if num >= proxy_num:
            return True
        return False

    @staticmethod
    def in_pool(ip_port):
        """判断是否在池中"""
        if proxy_pool.get(ip_port):
            return True
        return False

    @staticmethod
    def get_random_proxy():
        """"""
        ip_port = random.sample(proxy_pool.keys(), 1)[0]
        proxy_json = proxy_pool[ip_port]
        return ip_port, proxy_json

    @staticmethod
    def pack_proxy(ip_port):
        return {
            "http": f"http://{ip_port}",
            "https": f"https://{ip_port}"
        }

    # 判断是否过期：1. 没过期，返回ip_port；2. 过期：删除，封装，返回
    def get_one_proxy(self):
        _is_pool_num = self.is_pool_num()
        if _is_pool_num:
            ip_port, proxy_json = self.get_random_proxy()
            _is_expire = self.is_expire(proxy_json)
            if not _is_expire:
                return self.pack_proxy(ip_port)
            else:
                logger.warning("proxy expire: " + ip_port)
                proxy_pool.pop(ip_port, None)
                ip_port = self.remove_proxy(ip_port, proxy_json)
                return self.pack_proxy(ip_port)
        ip_port = self.remove_proxy(last_proxy["ip_port"], last_proxy["proxy_json"])
        return self.pack_proxy(ip_port)

    def process_request(self, request, spider):
        # 数据上传接口不走代理
        if "precheck" in request.url:
            return None
        proxies = self.get_one_proxy()
        # proxies = {"http": "http://122.51.192.40:1234", "https": "https://122.51.192.40:1234"}
        if request.url.startswith("http"):
            request.meta['proxy'] = proxies["http"]
        elif request.url.startswith("https"):
            request.meta['proxy'] = proxies["https"]
        else:
            raise Exception("MyProxyMiddleware: 协议错误")
        logger.info("using proxy: {}".format(request.meta['proxy']))
        return None


class MyRetryMiddleware(RetryMiddleware):
    # IOError is raised by the HttpCompression middleware when trying to
    # decompress an empty response
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TunnelError)
    PROXY_EXCEPTIONS_TO_RETRY = (ConnectionRefusedError,)

    def __init__(self, settings):
        RetryMiddleware.__init__(self, settings)
        self.retry_proxy_codes = set(int(x) for x in settings.getlist('RETRY_PROXY_CODES'))

    @staticmethod
    def remove_proxy(request):
        proxy = request.meta.get("proxy")
        ip_port = proxy.split("//")[1]
        proxy_pool.pop(ip_port, None)
        logger.warning("proxy not available: " + ip_port)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            # 状态码是由封ip产生的情况-删除ip-重试
            if response.status in self.retry_proxy_codes:
                self.remove_proxy(request)
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        if (
            isinstance(exception, self.EXCEPTIONS_TO_RETRY)
            and not request.meta.get('dont_retry', False)
        ):
            return self._retry(request, exception, spider)
        # 状态码是由代理异常产生的情况-删除ip-重试
        elif (
            isinstance(exception, self.PROXY_EXCEPTIONS_TO_RETRY)
            and not request.meta.get('dont_retry', False)
        ):
            self.remove_proxy(request)
            return self._retry(request, exception, spider)


class TemplatespiderSpiderMiddleware:
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
        spider.logger.info('Spider opened: %s' % spider.name)


class TemplatespiderDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

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
        spider.logger.info('Spider opened: %s' % spider.name)
