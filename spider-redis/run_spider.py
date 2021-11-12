#!/usr/bin/env python
# encoding: utf-8
"""
File Description: 
Author: nghuyong
Mail: nghuyong@163.com
Created Time: 2019-12-07 21:27
"""
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.heimaotousu import HeiMaoTouSuSpider
from spiders.comment import CommentSpider

if __name__ == '__main__':
    # insert_company()
    # mode = sys.argv[1]
    # init_comment_spider()
    os.environ['SCRAPY_SETTINGS_MODULE'] = f'settings'
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(HeiMaoTouSuSpider)
    process.crawl(CommentSpider)
    # the script will block here until the crawling is finished
    process.start()
