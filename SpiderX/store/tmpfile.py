#coding=utf-8
import os
from settings import TMP_FILES_DIR
from core.const import TASK_DIR
from utils.taskfinder import find_taskname

from ._base import BaseStore

TASK_PATH = os.path.sep.join([os.getcwd(),TASK_DIR])


class TmpFiles(BaseStore):
    __dir = TMP_FILES_DIR

    def __init__(self,filename):
        self.status = False
        # 分配一个名字 会绑定一个文件
        taskname = find_taskname(TASK_PATH)
        path = os.path.sep.join([TmpFiles.__dir,taskname])
        if not os.path.exists(path):
            os.makedirs(path)
        self.filename = os.path.sep.join([path,filename])

    def save(self,method ,*args,**kwargs):
        with open(self.filename,'wb') as f:
            method(f,*args,**kwargs)
        self.status = True

    def remove(self):
        if self.status is True:
            os.remove(self.filename)


class SaveFiles(BaseStore):

    def __init__(self, base_path, relative_path):
        full_path = os.path.abspath(os.path.join(base_path,relative_path))
        dirname = os.path.dirname(full_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        self.filename = full_path

    def save(self,method,*args,**kwargs):
        with open(self.filename,'wb') as f:
            method(f,*args,**kwargs)