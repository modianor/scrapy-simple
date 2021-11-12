#!/usr/bin/env python
# encoding: utf-8
"""
File Description: 
Author: nghuyong
Mail: nghuyong@163.com
Created Time: 2020/4/9
"""
import pymongo
from pymongo.errors import DuplicateKeyError

mongo_client = pymongo.MongoClient(host='localhost')
collection = mongo_client["weibo"]["account"]


def insert_cookie(username, password, cookie_str):
    """
    insert cookie to database
    :param username: username of weibo account
    :param password: password of weibo account
    :param cookie_str: cookie str
    :return:
    """
    try:
        collection.insert(
            {"_id": username, "password": password, "cookie": cookie_str, "status": "success"})
    except DuplicateKeyError as e:
        collection.find_one_and_update({'_id': username}, {'$set': {'cookie': cookie_str, "status": "success"}})


if __name__ == '__main__':
    # You can add cookie manually by the following code, change the value !!
    insert_cookie(
        username='18100695026',
        password='2482510236mdmdmd',
        cookie_str='_T_WM=e4ea93bd2a0f18f663a51a2949ec3d19; SUB=_2A25MRx42DeRhGeNG71IW8i3Jyj-IHXVvy6J-rDV6PUJbktAKLXLekW1NS0HRq5nURFXPLW5YzbcY40SC5igR_Sw3; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFO3hl2a9w1muKIbZXS0R2H5NHD95Qf1hB7S0z0SK20Ws4DqcjlKGHowCfCIgSQqPi.McvV; SSOLoginState=1631809126'
    )
