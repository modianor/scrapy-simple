import json
import random

from scrapy import Request


class TaskStatus:
    SUCCESS = 4
    FAIL = 5


class Task(object):

    def __init__(self, task_id=0, parent_task_id=0, spider_name='', task_type='', url='', param1='', param2='',
                 param3='', filter=False,
                 task_status=TaskStatus.SUCCESS,
                 exception='',
                 data=None, kibanalog='', request=None) -> None:
        self.task_id = random.randint(10000000000, 99999999999)
        self.parent_task_id = random.randint(10000000000, 99999999999)
        self.spider_name = spider_name
        self.task_type = task_type
        self.url = url
        self.param1 = param1
        self.param2 = param2
        self.param3 = param3
        self.task_status = task_status
        self.filter = filter
        self.exception = exception
        self.data = data
        self.kibanalog = kibanalog
        self.request = Request(request) if request else None
        self.response = None

    @classmethod
    def from_json(cls, task_params):
        return cls(**task_params)

    def __str__(self) -> str:
        data = {
            'spider_name': self.spider_name,
            'task_type': self.task_type,
            'url': self.url,
            'param1': self.param1,
            'param2': self.param2,
            'param3': self.param3,
            'task_status': self.task_status,
            'filter': self.filter,
            'exception': self.exception,
            'data': self.data,
            'kibanalog': self.kibanalog
        }
        return json.dumps(data, ensure_ascii=False)

    def to_dict(self):
        data = {
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'spider_name': self.spider_name,
            'task_type': self.task_type,
            'url': self.url,
            'param1': self.param1,
            'param2': self.param2,
            'param3': self.param3,
            'task_status': self.task_status,
            'filter': self.filter,
            'exception': self.exception,
            'data': self.data,
            'kibanalog': self.kibanalog,
            'request': self.request,
        }
        return data

    def copy(self):
        """Return a copy of this Task"""
        return self.replace()

    def replace(self, *args, **kwargs):
        """Create a new Request with the same attributes except for those
        given new values.
        """
        for x in ['task_id', 'parent_task_id', 'spider_name', 'task_type', 'url', 'param1', 'param2', 'param3',
                  'task_status', 'filter',
                  'exception', 'data', 'kibanalog']:
            kwargs.setdefault(x, getattr(self, x))
        cls = kwargs.pop('cls', self.__class__)
        return cls(*args, **kwargs)
