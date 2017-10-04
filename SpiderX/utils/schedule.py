#coding=utf-8
from datetime import datetime,timedelta

class BaseSchedule(object):

    def schedule(self,scheduler):
        raise NotImplementedError


class StartSoon(BaseSchedule):
    def __init__(self,seconds=None,minutes=None,hours=None):
        kwargs = {}
        if seconds is not None:
            kwargs['seconds'] = seconds
        if minutes is not None:
            kwargs['minutes'] = minutes
        if hours is not None:
            kwargs['hours'] = hours
        if not kwargs:
            raise Exception('schedule initialize error')
        self.soon = timedelta(**kwargs)

    def schedule(self,scheduler,task):
        scheduler.add_job(task,datetime.now()+self.soon)

    def get_desc(self):
        return 'task will start in %s' % self.soon.strftime('%H hours %M minutes %S seconds')