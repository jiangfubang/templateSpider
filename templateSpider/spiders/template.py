import scrapy
import logging

logger = logging.getLogger(__name__)

__author__ = 'jiangfb'

class TemplateSpider(scrapy.Spider):
    name = 'template'
    # allowed_domains = ['template.com']
    # start_urls = ['http://template.com/']

    def start_requests(self):
        yield scrapy.Request(
            url="https://www.baidu.com",
            callback=self.parse_desc,
            dont_filter=True,
        )

    def parse_desc(self, response):
        logger.info(response.text)
