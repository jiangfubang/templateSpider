# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import datetime
import json
import logging
import requests
import random

from scrapy import signals
from templateSpider.common.conf import proxy_ip_url
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from templateSpider.settings import TEMP_PROXY_IP

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
    def datestr_to_datetime(timeStr):
        return datetime.datetime.strptime(timeStr, '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_now_datetime():
        return datetime.datetime.now()

    def is_expire(self, proxy_json):
        expire_time_str = proxy_json["data"]["expire_time"]
        expire_time = self.datestr_to_datetime(expire_time_str)
        now_time = self.get_now_datetime()
        if expire_time < now_time:
            return True
        return False

    @staticmethod
    def remove_proxy(ip_port, proxy_json):
        if TEMP_PROXY_IP.get(ip_port):
            del TEMP_PROXY_IP[ip_port]
        res = requests.get(url=proxy_ip_url, data=json.dumps(proxy_json, ensure_ascii=False).encode("utf-8"), timeout=20)
        logger.warning("proxy expire: " + res.text)
        return res

    @staticmethod
    def request_proxy():
        return requests.get(url=proxy_ip_url)

    @staticmethod
    def pack_proxy(res):
        res_json = res.json()
        ip = res_json["data"]["ip"]
        port = str(res_json["data"]["port"])
        ip_port = ip + ":" + port
        TEMP_PROXY_IP[ip_port] = res_json
        return ip_port

    # 判断是否过期：1. 没过期，返回ip_port；2. 过期：删除，封装，返回
    def get_one_proxy(self):
        if len(TEMP_PROXY_IP)>2:
            ip_port = random.sample(TEMP_PROXY_IP.keys(), 1)[0]
            proxy_json = TEMP_PROXY_IP[ip_port]
            _is_expire = self.is_expire(proxy_json=proxy_json)
            if not _is_expire:
                return ip_port
            else:
                res = self.remove_proxy(ip_port, proxy_json)
                ip_port = self.pack_proxy(res)
                return ip_port
        res = self.request_proxy()
        ip_port = self.pack_proxy(res)
        return ip_port

    def process_request(self, request, spider):
        # 数据上传接口不走代理
        if "precheck" in request.url:
            return None
        ip_port = self.get_one_proxy()
        # ip_port = "122.51.192.40:1234"
        if request.url.startswith("http://"):
            request.meta['proxy'] = "http://{proxy_ip}".format(proxy_ip=ip_port)
        elif request.url.startswith("https://"):
            request.meta['proxy'] = "https://{proxy_ip}".format(proxy_ip=ip_port)
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
    def pack_proxy(res):
        res_json = res.json()
        ip = res_json["data"]["ip"]
        port = str(res_json["data"]["port"])
        ip_port = ip + ":" + port
        TEMP_PROXY_IP[ip_port] = res_json
        return ip_port

    def remove_proxy(self, ip_port):
        proxy_json = TEMP_PROXY_IP.get(ip_port)
        if proxy_json:
            del TEMP_PROXY_IP[ip_port]
            res = requests.get(url=proxy_ip_url, data=json.dumps(proxy_json, ensure_ascii=False).encode("utf-8"), timeout=20)
            self.pack_proxy(res)
            logger.warning("change proxy: " + res.text)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            # 状态码是由封ip产生的情况-删除ip-重试
            if response.status in self.retry_proxy_codes:
                proxy = request.meta.get("proxy")
                ip_port = proxy.split("//")[1]
                self.remove_proxy(ip_port)
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response



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
