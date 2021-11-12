# -*- coding: utf-8 -*-
import pymongo
from pymongo.errors import DuplicateKeyError
from items import RelationshipItem, TweetItem, UserItem, CommentItem
from settings import MONGO_HOST, MONGO_PORT


class MongoDBPipeline(object):
    def __init__(self):
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        db = client['crawler']
        self.Comments = db["crawler_weibo_comment"]
        self.Complaint = db["crawler_sina_tousu"]

    def process_item(self, item, spider):
        if spider.name == 'comment_spider':
            self.insert_item(self.Comments, item)
        if spider.name == 'heimaotousu_spider':
            self.insert_item(self.Complaint, item)
        return item

    def process_task(self, task, spider):
        pass

    @staticmethod
    def insert_item(collection, item):
        try:
            collection.insert(dict(item))
        except DuplicateKeyError:
            pass
