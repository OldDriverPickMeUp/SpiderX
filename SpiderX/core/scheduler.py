#coding=utf-8

import threading
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import pytz
from .const import TIME_ZONE


class TaskScheduler(object):
    _lock = threading.Lock()
    _job_defaults = {
             'coalesce': True,
            'max_instances': 1,
        }

    @staticmethod
    def scheduler():
        if not hasattr(TaskScheduler,'_scheduler'):
            TaskScheduler._lock.acquire()
            if not hasattr(TaskScheduler,'_scheduler'):
                TaskScheduler._scheduler = BlockingScheduler(job_defaults = TaskScheduler._job_defaults,timezone=pytz.timezone(TIME_ZONE))
            TaskScheduler._lock.release()
        return TaskScheduler._scheduler

    @staticmethod
    def trigger(trigger_type,**kwargs):
        # 在修改job的触发器时必须加载时区
        if 'timezone' not in kwargs:
            kwargs['timezone'] = pytz.timezone(TIME_ZONE)
        if trigger_type=='cron':
            return CronTrigger(**kwargs)
        elif trigger_type=='interval':
            return IntervalTrigger(**kwargs)

