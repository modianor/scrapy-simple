import os
import shutil
import stat
import zipfile
from os.path import join, exists


def delete_file(filePath):
    if os.path.exists(filePath):
        for fileList in os.walk(filePath):
            for name in fileList[2]:
                os.chmod(os.path.join(fileList[0], name), stat.S_IWRITE)
                os.remove(os.path.join(fileList[0], name))
        shutil.rmtree(filePath)


def file2zip(zip_file_name: str, zip_file_dir: str):
    """ 将文件夹中文件压缩存储为zip
    """
    with zipfile.ZipFile(zip_file_name, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        file_names = os.listdir(zip_file_dir)
        for fn in file_names:
            parent_path, name = os.path.split(fn)
            zf.write(join(zip_file_dir, fn), arcname=name)


def data2zip(task):
    items = task.data
    dir_path = './Task_Data'
    policyId = task.spider_name
    task_id = task.task_id

    task_dir = f'{dir_path}/{policyId}'
    task_data_dir = f'{task_dir}/{task_id}'
    zip_name = join(task_dir, f'{task.task_id}.zip')

    if not exists(path=task_data_dir):
        os.makedirs(name=task_data_dir)

    for name in items:
        value = items[name]
        file_path = join(task_data_dir, name)
        with open(file_path, 'w') as f:
            f.write(value)

    file2zip(zip_name, task_data_dir)
    delete_file(task_data_dir)
