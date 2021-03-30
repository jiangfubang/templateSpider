# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name:       main
   Description :
   Author:          jiangfb
   date:            2021-03-30
-------------------------------------------------
   Change Activity:
                    2021-03-30:
-------------------------------------------------
"""
from scrapy import cmdline

__author__ = 'jiangfb'

if __name__ == '__main__':
    cmdline.execute(["scrapy", "crawl", "template"])