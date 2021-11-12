# -*- coding: utf-8 -*-
import logging

import logstash

from scrapy.utils.fileoperator import data2zip
from scrapy.utils.task_process import upload_task

task_logger = logging.getLogger('scrapy_venom')
task_logger.addHandler(logstash.TCPLogstashHandler('localhost', 5000, version=1))


class TaskPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        try:
            pipe = cls.from_settings(crawler.settings)
        except AttributeError:
            pipe = cls()
        pipe.crawler = crawler
        return pipe

    def process_task(self, task, spider):
        if task.task_type == 'Detail' and task.data:
            data2zip(task)
        upload_task(task.to_dict())
        spider.logger.info(f'process task: {str(task)}')
        return task
