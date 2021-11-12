#!/usr/bin/env python
# encoding: utf-8
"""
File Description: 
Author: nghuyong
Mail: nghuyong@163.com
Created Time: 2020/4/14
"""
import json
import re
import time
import traceback

from lxml import etree

from scrapy import FormRequest
from scrapy.task import Task, TaskStatus
from scrapy_redis.spiders import RedisSpider


class CommentSpider(RedisSpider):
    name = "comment_spider"
    base_url = "https://weibo.cn"
    redis_key = "comment_spider:start_urls"

    def get_task(self, response):
        try:
            task = response.request.task
            return task
        except:
            return Task(spider_name=self.name, url=response.url, task_type=TaskStatus.FAIL)

    def set_task(self, task, status):
        task.task_status = status

    def make_request_from_data(self, data):
        data = json.loads(data)
        task = Task.from_json(data)
        return FormRequest(task=task, method='GET', priority=10, callback=self.parse)

    def parse(self, response):
        try:
            task = self.get_task(response)
            if response.url.endswith('page=1'):
                all_page = re.search(r'/>&nbsp;1/(\d+)页</div>', response.text)
                if all_page:
                    all_page = all_page.group(1)
                    all_page = int(all_page)
                    all_page = all_page if all_page <= 50 else 50
                    for page_num in range(2, all_page + 1):
                        page_url = response.url.replace('page=1', 'page={}'.format(page_num))
                        next_task = Task(spider_name='comment_spider', task_type='Detail', url=page_url)
                        yield FormRequest(next_task, self.parse, formdata={}, method='GET',
                                          dont_filter=next_task.filter,
                                          meta=response.meta,
                                          callback=self.parse_item)
                self.set_task(task, TaskStatus.SUCCESS)
                kibanalog = f'name:{self.name} callback:parse {task.task_type}生成任务:{50}'
            else:
                kibanalog = f'name:{self.name} callback:parse {task.task_type}生成失败任务'
            task.kibanalog = kibanalog
            yield task
        except:
            kibanalog = f'name:{self.name} callback:parse exception:\n{traceback.format_exc()}'
            task.kibanalog = kibanalog
            yield task

    def parse_item(self, response):
        try:
            task = self.get_task(response)
            tree_node = etree.HTML(response.body)
            comment_nodes = tree_node.xpath('//div[@class="c" and contains(@id,"C_")]')
            for comment_node in comment_nodes:
                comment_user_url = comment_node.xpath('.//a[contains(@href,"/u/")]/@href')
                if not comment_user_url:
                    continue
                comment_item = dict()
                comment_item['crawl_time'] = int(time.time())
                comment_item['weibo_id'] = response.url.split('/')[-1].split('?')[0]
                comment_item['comment_user_id'] = re.search(r'/u/(\d+)', comment_user_url[0]).group(1)
                # comment_item['content'] = extract_comment_content(etree.tostring(comment_node, encoding='unicode'))
                comment_item['_id'] = comment_node.xpath('./@id')[0]
                created_at_info = comment_node.xpath('.//span[@class="ct"]/text()')[0]
                like_num = comment_node.xpath('.//a[contains(text(),"赞[")]/text()')[-1]
                comment_item['like_num'] = int(re.search('\d+', like_num).group())
                # comment_item['created_at'] = time_fix(created_at_info.split('\xa0')[0])
                yield comment_item
                item_task = task.copy()
                item_task.kibanalog = f'name:{self.name} callback:parse_item task_type:{item_task.task_type} 任务状态:成功'
                yield item_task
        except:
            kibanalog = f'name:{self.name} callback:parse_item exception:\n{traceback.format_exc()}'
            task.kibanalog = kibanalog
            yield task
