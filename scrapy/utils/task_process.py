import requests

from scrapy.utils.reqser import request_to_dict, request_from_dict

headers = {
    'authority': 'n.sinaimg.cn',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
    'accept': '*/*',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-dest': 'script',
    'referer': 'https://tousu.sina.com.cn/',
    'accept-language': 'zh-CN,zh;q=0.9',
    'contentType': 'application/x-www-form-urlencoded;charset=UTF-8',
}


def upload_request(request, spider):
    task_dict = request_to_dict(request, spider)
    return upload_task(task_dict)


def upload_task(task_dict):
    response = requests.post(url='http://localhost:6048/task/upload', headers=headers, data=task_dict)
    return True


def get_task(spider_name, task_type, spider):
    try:
        params = {
            'spider_name': spider_name,
            'task_type': task_type
        }
        response = requests.get(url='http://localhost:6048/task/getTask', headers=headers, params=params)
        json_data = response.json()
        request = request_from_dict(json_data, spider)
        return request
    except:
        return None
