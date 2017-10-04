#coding=utf-8

import os,json

from settings import JSON_STORE_DIR
from core.const import TASK_DIR
from core.error import CoreError
from utils.taskfinder import find_taskname
from ._base import BaseStore

TASK_PATH = os.path.sep.join([os.getcwd(),TASK_DIR])

class JsonStore(BaseStore):
    __dir = JSON_STORE_DIR
    __post_fix = 'json'
    def __init__(self,name='default'):
        # 分配一个名字 会绑定一个文件
        taskname = find_taskname(TASK_PATH)
        if taskname is None:
            raise CoreError('didn\'t find task')
        path = os.path.sep.join([JsonStore.__dir,taskname])
        if not os.path.exists(path):
            os.makedirs(path)
        filename = '.'.join([name,JsonStore.__post_fix])
        self.filename = os.path.sep.join([path,filename])
        if os.path.exists(self.filename):
            with open(self.filename,'r') as f:
                try:
                    self.data = json.load(f)
                except:
                    self.data = {}
        else:
            self.data={}

    def set(self,key,obj):
        self.data[key] = obj

    def get(self,key):
        return self.data.get(key)

    def save(self):
        with open(self.filename,'w') as f:
            json.dump(self.data,f)

