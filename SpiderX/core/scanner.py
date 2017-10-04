#coding=utf-8

"""
要扫描task文件夹下所有的任务
要扫描task文件夹下所有的子文件夹中main.py的UpdateTask类
构造dbrouter和logrouter
"""
import os
import importlib

import task,orm
from .const import TASK_DIR
from .model import BaseModel
from .scheduler import TaskScheduler
from .corelogger import CoreLogger,DBLogger
from dao.daofactory import DaoFactory
from datetime import datetime,timedelta

if os.path.abspath(os.path.sep.join([os.getcwd(),'core']))!=os.path.dirname(os.path.abspath(__file__)):
    raise Exception('you should start from this project\'s root folder')

BASE_TASK = task.UpdateTask
ALL_BASE_TASK = [obj for obj in vars(task).values() if hasattr(obj, '__base__') and issubclass(obj,BASE_TASK)]


class Scaner(object):
    __path = os.path.sep.join([os.getcwd(),TASK_DIR])

    @staticmethod
    def scan():
        CoreLogger.log(task='starting', message='in debug mode')
        CoreLogger.log(task='scanning',message='start scan tasks')
        all_tasks = [n.split(os.path.sep)[-1] for n in os.listdir(Scaner.__path) if not n.startswith('_') and not n.startswith('.')]
        all_task_dir = ['.'.join([TASK_DIR,n,'main']) for n in all_tasks]
        all_task_module = [importlib.import_module(n) for n in all_task_dir]
        update_task_cls = {}
        update_task_db_models = {}
        for index,task_module in enumerate(all_task_module):
            for obj_name in dir(task_module):
                if obj_name.startswith('_'):
                    continue
                obj = getattr(task_module, obj_name)
                if hasattr(obj,'__base__') and obj not in ALL_BASE_TASK and issubclass(obj,BASE_TASK):
                    if hasattr(obj, 'debug') and obj.debug is True:
                        current_task = all_tasks[index]
                        CoreLogger.log(message='|---> find task %s in module %s' % (current_task,all_task_dir[index]),task='scanning')
                    # 在这里引入model的载入

                        db_models = Scaner.get_models(current_task)
                        obj._filename = all_task_dir[index]

                        update_task_cls[current_task]=obj
                        DBLogger.set(current_task,getattr(obj,'author',None))
                        update_task_db_models[current_task] = db_models
        if len(update_task_cls)>1:
            raise Exception('task %s are all in debug mode.there only can be single task in debug mode.' % ','.join(update_task_cls.keys()))
        if update_task_cls:
            Scaner._task_cls = update_task_cls
            Scaner._task_db_model = update_task_db_models
        else:
            CoreLogger.warning('scanning','find no tasks process will end')
            return -1
        CoreLogger.log('scanning', 'task %s will be executed in 5 seconds' % update_task_cls.items()[0][0])
        Scaner.build()


    @staticmethod
    def build():
        # 生成每个任务的dbroute和logroute
        # 载入logger
        if True or hasattr(Scaner,'_task_cls'):
            CoreLogger.log(message='building basic config', task='building')
            for task_name in Scaner._task_cls:
                current_task_cls = Scaner._task_cls[task_name]
                current_task_cls.name = task_name
                CoreLogger.log(message='|---> building task %s\' basic config' % task_name,task='building')
                conn_path = getattr(current_task_cls, 'conn_path', None)
                if conn_path is None:
                    conn_path = 'default'
                if not DaoFactory.have_conn(conn_path):
                    raise Exception('don\'t have database conn_path named %s' % conn_path)
                # 检查conn_path 合法性
                # 为 db_models 载入db配置
                db_models = Scaner._task_db_model[task_name]
                for model in db_models:
                    if getattr(model,'_conn_name',None) is None:
                        setattr(model,'_conn_name',conn_path)
                        CoreLogger.log(message='    |---> linking model %s to conn_path %s' % (model.__name__,conn_path),
                                      task='building')
                    else:
                        CoreLogger.log(message='    |---> linking model %s to conn_path %s' % (model.__name__, getattr(model,'_conn_name')),
                                      task='building')
                # adding task
                CoreLogger.log('debuging','%s started' % task_name)
                current_task_cls.run()
                CoreLogger.log('debuging', '%s ended' % task_name)

        else:
            raise Exception('scan no task ')


    @staticmethod
    def get_models(task_name):
        model_dir = '.'.join([TASK_DIR,task_name,'model'])
        try:
            model_module = importlib.import_module(model_dir)
            models = []
            for obj_name in dir(model_module):
                if obj_name.startswith('_'):
                    continue
                obj = getattr(model_module, obj_name)
                if hasattr(obj, '__base__') and obj is not BaseModel and issubclass(obj,BaseModel):
                    CoreLogger.log(message='    |---> find model %s for task %s' % (obj_name, task_name),
                                   task='scanning')
                    models.append(obj)
                elif hasattr(obj,'__base__') and obj.__base__ is orm.Model:
                    #print 'asad'
                    CoreLogger.log(message='    |---> find new type orm model %s for task %s' % (obj_name, task_name),
                                   task='scanning')
                    models.append(obj)
            return models
        except:
            CoreLogger.warning(message='    |---> find no model for task %s abort' % task_name, task='scanning')
            return []

