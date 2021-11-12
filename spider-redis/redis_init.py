#!/usr/bin/env python
# encoding: utf-8
"""
File Description: 
Author: nghuyong
Mail: nghuyong@163.com
Created Time: 2020/4/15
"""
import datetime
import json

import redis

from scrapy.task import Task


def redis_init(spider_name, tasks):
    r = redis.Redis(host='localhost')
    for key in r.scan_iter(f"{spider_name}*"):
        r.delete(key)
    print(f'Add urls to {spider_name}:start_urls')
    for task in tasks:
        r.lpush(f'{spider_name}:start_urls', str(task))
        print('Added:', task.url)


def init_user_spider():
    # change the user ids
    user_ids = ['1087770692', '1699432410', '1266321801']
    urls = [f"https://weibo.cn/{user_id}/info" for user_id in user_ids]
    redis_init('user_spider', urls)


def init_fan_spider():
    # change the user ids
    user_ids = ['1087770692', '1699432410', '1266321801']
    urls = [f"https://weibo.cn/{user_id}/fans?page=1" for user_id in user_ids]
    redis_init('fan_spider', urls)


def init_follow_spider():
    # change the user ids
    user_ids = ['1087770692', '1699432410', '1266321801']
    urls = [f"https://weibo.cn/{user_id}/follow?page=1" for user_id in user_ids]
    redis_init('follower_spider', urls)


def init_comment_spider():
    # change the tweet ids
    # tweet_ids = ['IDl56i8av', 'IDkNerVCG', 'IDkJ83QaY', 'IDl56i8av', 'IDkNerVCG', 'IDkJ83QaY', 'IDl56i8av', 'IDkNerVCG',
    #              'IDkJ83QaY', 'IDl56i8av', 'IDkNerVCG', 'IDkJ83QaY', 'IDl56i8av', 'IDkNerVCG', 'IDkJ83QaY']
    tweet_ids = ['IDl56i8av']
    tasks = [Task(spider_name='comment_spider', task_type='List', filter=True,
                  url=f"https://weibo.cn/comment/hot/{tweet_id}?rl=1&page=1") for tweet_id in tweet_ids]
    redis_init('comment_spider', tasks)


def init_heimao_spider():
    # change the tweet ids
    urls = [Task(spider_name='heimaotousu_spider', task_type='List', filter=True,
                 url="https://tousu.sina.com.cn/api/company/main_search?sort_col=4&sort_ord=2&page_size=10&page=1&_=1632714612466")
            ]
    redis_init('heimaotousu_spider', urls)


def init_user_tweets_spider():
    # crawl tweets post by users
    user_ids = ['1087770692', '1699432410', '1266321801']
    tasks = [Task(spider_name='tweets_spider', task_type='List', filter=True,
                  url=f'https://weibo.cn/{user_id}/profile?page=1') for user_id in user_ids]
    redis_init('tweet_spider', tasks)


def init_keyword_tweets_spider():
    # crawl tweets include keywords in a period, you can change the following keywords and date
    keywords = ['转基因']
    date_start = datetime.datetime.strptime("2017-07-30", '%Y-%m-%d')
    date_end = datetime.datetime.strptime("2018-07-30", '%Y-%m-%d')
    time_spread = datetime.timedelta(days=1)
    urls = []
    url_format = "https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}" \
                 "&advancedfilter=1&starttime={}&endtime={}&sort=time&page=1"
    while date_start < date_end:
        next_time = date_start + time_spread
        urls.extend(
            [url_format.format(keyword, date_start.strftime("%Y%m%d"), next_time.strftime("%Y%m%d"))
             for keyword in keywords]
        )
        date_start = next_time
    redis_init('tweet_spider', urls)


if __name__ == '__main__':
    init_heimao_spider()
    # init_user_tweets_spider()
