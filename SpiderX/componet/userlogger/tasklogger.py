#coding=utf-8
import os,threading
from datetime import datetime
from core.const import TASK_DIR
from utils.taskfinder import find_taskname
from ._base import BaseLog
from core.corelogger import DBLogger,CoreLogger
TASK_PATH = os.path.sep.join([os.getcwd(),TASK_DIR])


class TaskLogger(BaseLog):
    """
    生成如下格式log
    [E task time] trace(filename->funcname) message
    [I task time] message
    [W task time] message
    """
    error_partten = '[E {0} {1}] {2}'
    info_partten= '[I {0} {1}] {2}'
    warning_partten = '[W {0} {1}] {2}'
    __lock = threading.Lock()

    @staticmethod
    def log(message):
        task_name = find_taskname(TASK_PATH)
        TaskLogger.__lock.acquire()
        log_str = TaskLogger.info_partten.format(task_name, BaseLog.now_time(), message)
        BaseLog.log(log_str)
        TaskLogger.__lock.release()

    @staticmethod
    def error(message=None,error=None):
        task_name = find_taskname(TASK_PATH)
        error_str = '%s:%s' % (error.__class__.__name__,error.message) if error else ''
        real_message = '%s %s' % (message if message else '',error_str)
        TaskLogger.__lock.acquire()
        log_str = TaskLogger.error_partten.format(task_name,BaseLog.now_time(), real_message)
        BaseLog.error(log_str)
        TaskLogger.__lock.release()

    @staticmethod
    def warning(message):
        task_name = find_taskname(TASK_PATH)
        TaskLogger.__lock.acquire()
        log_str = TaskLogger.warning_partten.format(task_name, BaseLog.now_time(), message)
        BaseLog.log(log_str)
        TaskLogger.__lock.release()

    @staticmethod
    def dblog(message):
        task_name = find_taskname(TASK_PATH)
        try:
            DBLogger.log(task_name, message, datetime.now())
        except Exception as e:
            CoreLogger.error('DBLogging', '%s:%s' % (e.__class__.__name__, e.message))