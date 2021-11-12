# encoding: utf-8
import base64
import random
import time

import pymongo
from settings import MONGO_PORT, MONGO_HOST, ABUYUN_SOCIAL_MEDIA_PROXY_USERNAME, ABUYUN_SOCIAL_MEDIA_PROXY_PASSWORD


class CookieMiddleware(object):
    """
    每次请求都随机从账号池中选择一个账号去访问
    """

    def __init__(self):
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        self.account_collection = client['weibo']['account']

    def process_request(self, request, spider):
        all_count = self.account_collection.find({}).count()
        if all_count == 0:
            raise Exception('Current account pool is empty!! The spider will stop!!')
        random_index = random.randint(0, all_count - 1)
        random_account = self.account_collection.find({})[random_index]
        request.headers.setdefault('Cookie', random_account['cookie'])
        request.meta['account'] = random_account


class RedirectMiddleware(object):
    """
    check account status
    HTTP Code = 302/418 -> cookie is expired or banned, and account status will change to 'error'
    """

    def __init__(self):
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        self.account_collection = client['weibo']['account']

    def process_response(self, request, response, spider):
        http_code = response.status
        if http_code == 302 or http_code == 403:
            self.account_collection.find_one_and_update({'_id': request.meta['account']['_id']},
                                                        {'$set': {'status': 'error'}}, )
            return request
        elif http_code == 418:
            spider.logger.error('IP Proxy is invalid, please change the ip proxy or stop the programme!')
            return request
        else:
            return response


class IPProxyMiddleware(object):
    proxyServer = "http://http-dyn.abuyun.com:9020"

    @classmethod
    def from_crawler(cls, crawler):
        return cls(ABUYUN_SOCIAL_MEDIA_PROXY_USERNAME,
                   ABUYUN_SOCIAL_MEDIA_PROXY_PASSWORD)

    def __init__(self, proxy_user, proxy_pass):
        self.proxyAuth = "Basic " + base64.urlsafe_b64encode(bytes((proxy_user + ":" + proxy_pass), "ascii")).decode(
            "utf8")

    def process_request(self, request, spider):
        need_proxy_list = getattr(spider, 'need_proxy_list', [])
        if any([i for i in need_proxy_list if i in request.url]):
            request.meta["proxy"] = self.proxyServer
            request.headers["Proxy-Authorization"] = self.proxyAuth
            time.sleep(1 / 5)

    def process_response(self, request, response, spider):
        retry_status_codes = getattr(spider, 'retry_status_codes', [])
        if response.status in retry_status_codes:
            return request
        else:
            return response
