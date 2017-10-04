#coding=utf-8
from core.corelogger import now_log_time
from core.corelogger import core_log_imp


class BaseLog(object):
    @staticmethod
    def now_time():
        return now_log_time()

    @staticmethod
    def log(message):
        core_log_imp(message)

    @staticmethod
    def error(message):
        core_log_imp(message)

    @staticmethod
    def warning(message):
        core_log_imp(message)