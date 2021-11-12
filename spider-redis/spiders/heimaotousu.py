#!/usr/bin/env python
# encoding: utf-8
"""
File Description: 
Author: nghuyong
Mail: nghuyong@163.com
Created Time: 2020/4/14
"""
import datetime
import hashlib
import json
import re
import time
import traceback

import requests
from bs4 import BeautifulSoup
from pymongo.collection import Collection

from scrapy import FormRequest
from scrapy.task import Task, TaskStatus
from scrapy_redis.spiders import RedisSpider


def get_mongo_connection(mongourl='mongodb://localhost:27017/admin', dbname='crawler', **mongo_args):
    import pymongo
    client = pymongo.MongoClient(mongourl, **mongo_args)
    db = client[dbname]
    return db


class HeiMaoTouSuSpider(RedisSpider):
    name = "heimaotousu_spider"
    base_url = "https://weibo.cn"
    redis_key = "heimaotousu_spider:start_urls"

    db = get_mongo_connection()

    start_time = datetime.datetime.utcnow()
    spider_config_dict = {
        'heimaotousu': ('黑猫投诉', 'crawler.crawler_sina_tousu'),
    }
    need_proxy_list = ['tousu.sina.com.cn']

    complaint_status = {
        1: '通过审核',
        3: '待分配',
        4: '处理中',
        6: '已回复',
        7: '已完成',
        8: '已关闭',
    }

    last_update_time = ''

    # logging.getLogger('scrapy').propagate = False

    headers = {
        # 'authority': 'n.sinaimg.cn',
        # 'pragma': 'no-cache',
        # 'cache-control': 'no-cache',
        # 'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
        # 'accept': '*/*',
        # 'x-requested-with': 'XMLHttpRequest',
        # 'sec-ch-ua-mobile': '?0',
        # 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
        # 'sec-ch-ua-platform': '"macOS"',
        # 'sec-fetch-site': 'cross-site',
        # 'sec-fetch-mode': 'no-cors',
        # 'sec-fetch-dest': 'script',
        # 'referer': 'https://tousu.sina.com.cn/',
        # 'accept-language': 'zh-CN,zh;q=0.9',
    }

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
        param1 = json.loads(task.param1)
        uid = param1['uid']
        company_name = param1['title']

        try:
            url = 'https://tousu.sina.com.cn/api/company/received_complaints'
            last_update_time = self.get_last_time(product_name=company_name)
            timestamp = str(int(time.time() * 1000))
            params = self.init_params(couid=uid, c_type=str(1), page=str(1),
                                      timestamp=timestamp)
            item = dict()
            item['product_name'] = company_name
            task.url = url
            task.param2 = json.dumps(params, ensure_ascii=False)
            return FormRequest(task=task, method='GET', formdata=params, headers=self.headers, priority=10,
                               callback=self.parse, meta={
                    'item': item,
                    'uid': uid,
                    'last_update_time': last_update_time,
                    'company_name': company_name,
                })
        except:
            self.logger.error(f'店铺:{company_name}, uid:{uid}, 生成起始Request失败， 错误原因：{traceback.format_exc()}')

    def parse(self, response):
        p_task = Task()
        try:
            p_task = self.get_task(response)
            uid = response.meta['uid']
            company_name = response.meta['company_name']
            last_update_time = response.meta['last_update_time']
            page_nums = self.get_company_page_num(response.text)

            url = 'https://tousu.sina.com.cn/api/company/received_complaints'
            for page_num in range(page_nums):
                timestamp = str(int(time.time() * 1000))
                params = self.init_params(couid=uid, c_type=str(1), page=str(page_num + 1),
                                          timestamp=timestamp)
                item = dict()
                item['product_name'] = company_name
                param2 = json.dumps(params, ensure_ascii=False)
                c_task = Task(spider_name=self.name, url=url, param2=param2, task_type='List')
                yield FormRequest(task=c_task, method='GET', formdata=params, headers=self.headers, priority=10,
                                  callback=self.parse_list, meta={
                        'item': item,
                        'uid': uid,
                        'last_update_time': last_update_time,
                    })
            kibanalog = f'name:{self.name} callback:parse task_type:{p_task.task_type} 生成任务: {page_nums}条List任务'
            p_task.kibanalog = kibanalog
            yield p_task
        except:
            self.set_task(p_task, TaskStatus.FAIL)
            self.logger.error(traceback.format_exc())
            kibanalog = f'name:{self.name} callback:parse exception:\n{traceback.format_exc()}'
            p_task.kibanalog = kibanalog
            yield p_task

    def parse_list(self, response):
        p_task = Task()
        try:
            p_task = self.get_task(response)
            item = response.meta['item']
            last_update_time = response.meta['last_update_time']
            json_data = json.loads(response.text)
            complaints = json_data['result']['data']['complaints']

            if complaints is None:
                complaints = []

            pager = json_data['result']['data']['pager']
            current_page = pager['current']
            page_amount = pager['page_amount']

            self.logger.info('=' * 80)
            self.logger.info(pager)
            self.logger.info(
                f'公司:{item["product_name"]}, 最新更新日期:{last_update_time} 正在解析第{current_page}/{page_amount}'
                f'页投诉翻页,当前页{len(complaints)}条投诉')
            for complaint in complaints:
                # 解析投诉列表信息
                complaint_item = item.copy()
                complaint_item['url'] = 'https:' + complaint['main']['url']
                complaint_item['complaint_status'] = self.complaint_status[complaint['main']['status']]
                complaint_item['title'] = self.extract_text(complaint['main']['title'])
                complaint_item['comsumer_name'] = complaint['author']['title']
                complaint_item['wb_profile'] = 'https:' + complaint['author']['wb_profile']
                complaint_item['time'] = self.time_tanser(complaint['main']['timestamp'])

                if last_update_time > complaint_item['time']:
                    self.logger.warn(
                        f'公司:{item["product_name"]}, 标题：{complaint_item["title"]}, 最新更新日期:{last_update_time}, '
                        f'当前日期:{complaint_item["time"]}, 无需更新')
                    break

                self.logger.info(
                    f'公司:{item["product_name"]}, 更新标题：{complaint_item["title"]}, 最新更新日期:{last_update_time}, '
                    f'当前日期:{complaint_item["time"]}, 更新')

                abstract = {
                    'complaint_id': complaint['main']['sn'],
                    'complaint_target': self.extract_text(complaint['main']['cotitle']),
                    'appeal': complaint['main']['appeal'],
                    'amount_involved': float(complaint['main']['cost'])
                }
                complaint_item['abstract'] = abstract
                evaluate_u = complaint['main']['evaluate_u']

                # 生成解析详情页Request
                c_task = Task(spider_name=self.name, url=complaint_item['url'], task_type='Detail')
                yield FormRequest(task=c_task, method='GET', callback=self.parse_detail, dont_filter=True,
                                  headers=self.headers,
                                  priority=10, meta={
                        'item': complaint_item,
                        'evaluate_u': evaluate_u
                    })
            p_task.kibanalog = f'name:{self.name} callback:parse_list task_type:{p_task.task_type} 生成任务: {len(complaints)}条Detail任务'
            yield p_task
        except:
            self.set_task(p_task, TaskStatus.FAIL)
            self.logger.error(traceback.format_exc())
            p_task.kibanalog = f'name:{self.name} callback:parse_list exception:\n{traceback.format_exc()}'
            yield p_task

    def parse_detail(self, response):
        p_task = Task()
        try:
            p_task = self.get_task(response)
            item = response.meta['item']
            status = response.xpath('//ul[@class="ts-q-list"]/li[last()]/b/text()').get()
            abstract = item['abstract']
            abstract['status'] = status

            steplist = response.xpath('//div[@class="ts-d-item"]').getall()
            steps = list()
            for step in steplist:
                soup = BeautifulSoup(step, 'lxml')
                name = soup.find('span', {'class': 'u-name'}).text
                status = soup.find('span', {'class': 'u-status'}).text
                date = soup.find('span', {'class': 'u-date'}).text
                if '评价' in status:
                    evaluate_u = response.meta['evaluate_u']
                    content = f'服务态度: {evaluate_u["attitude"]}星,处理速度: {evaluate_u["process"]}星,满意度: {evaluate_u["satisfaction"]}星 \n {evaluate_u["evalContent"]}'
                else:
                    content = soup.find('div', {'class': 'ts-d-cont'}).text
                data = {
                    'name': name,
                    'status': status,
                    'date': date,
                    'detail': content,
                }
                steps.append(data)
            item['step_list'] = steps

            item['api_name'] = self.name

            relategroupts_url = response.xpath('//a[@data-sudaclick="relategroupts_view"]/@href').get()
            if relategroupts_url:
                item['group_complaint_id'] = re.search('.*?/view/(.*)', '/grp_comp/view/G17354926946').group(1)

            item['insert_time'] = datetime.datetime.utcnow()
            # yield item
            p_task.data = {'index.json': response.text}
            p_task.kibanalog = f'name:{self.name} callback:parse_detail task_type:{p_task.task_type} 任务状态:成功'
            yield p_task
        except:
            self.set_task(p_task, TaskStatus.FAIL)
            self.logger.error(traceback.format_exc())
            p_task.kibanalog = f'name:{self.name} callback:parse_detail exception:\n{traceback.format_exc()}'
            yield p_task

    def get_company_page(self, url):
        response = requests.get(url, headers=self.headers)
        json_data = response.json()
        return json_data

    def get_company_page_num(self, content):
        json_data = json.loads(content)
        page_nums = json_data['result']['data']['pager']['page_amount']
        if page_nums:
            if page_nums < 100:
                return page_nums
            else:
                return 100
        else:
            return 1

    # return page_nums if page_nums and page_nums < 100 else 100

    def get_complaint_page(self, url, params):
        response = requests.get(url, params=params, headers=self.headers)
        json_data = response.json()
        page_nums = json_data['result']['data']['pager']['page_amount']
        return page_nums
        # return page_nums if page_nums and page_nums < 100 else 100

    def get_complaint_page_num(self, url, params):
        page_nums = self.get_complaint_page(url, params)
        return page_nums

    def get_signature(self, params_list):
        params_list.sort()
        s = hashlib.sha256()
        s.update(''.join(params_list).encode('utf-8'))  # Hash the data.
        signature = s.hexdigest()
        return signature

    def init_params(self, couid, c_type='1', page='1', page_size='10', timestamp=''):
        random_str = 'QNT4vu8q79XzrcdM'
        const_str = '$d6eb7ff91ee257475%'

        params_list = [timestamp, random_str, couid, const_str, c_type, page_size, page]
        signature = self.get_signature(params_list)

        return {
            'ts': timestamp,
            'rs': random_str,
            'couid': couid,
            'type': str(c_type),
            "page_size": str(page_size),
            'page': str(page),
            'signature': signature
        }

    def time_tanser(self, timestamp):
        localtime = time.localtime(int(timestamp))
        time_ = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
        return time_

    def get_last_time(self, product_name):

        try:
            collection: Collection = self.db['crawler.crawler_sina_tousu']
            item = next(collection.find({'product_name': product_name}).sort([('time', -1)]).limit(1))
            # return item['time']
            return '2000-01-1 00:00:00'
        except StopIteration:
            return '2000-01-1 00:00:00'

    def extract_text(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()

    def insert_company(self, companies):
        try:
            collection: Collection = self.db['crawler.crawler_sina_tousu.company']
            collection.insert_many(companies)
            self.logger.info('插入成功')
        except:
            pass
