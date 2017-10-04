#coding=utf-8
import sys
from datetime import datetime
from .const import TIME_FORMAT,INSTANCE_NAME,DEFAULT_AUTHOR,DBLOGGER_ENABLE
from .parsecmd import StartCommend
import orm


@orm.build_model
class FatalLog(orm.Model):
    _table = 'fatal_log'
    _conn_name = 'default'
    _name = '致命错误表'
    id = orm.IntegerType(length=10,name='id',comment='主键',primary_key=True,unsigned=True,auto_increase=True,blank=False)
    instance = orm.CharType(length=22,name='instance',comment='实例名称', blank=False)
    task_name = orm.CharType(length=30,varchar=True,comment='任务名称', blank=False,name='task_name')
    author = orm.CharType(name='author',length=20,blank=False,comment='作者')
    traceback_str = orm.CharType(name='traceback_str',length=1000,varchar=True,comment='追踪信息',blank=True)
    log_time = orm.DatetimeType(name='log_time',comment='创建时间')
    related_url = orm.CharType(name='related_url',comment='相关url',length=512,varchar=True)


@orm.build_model
class SpiderPid(orm.Model):
    _table = 'spider_pid'
    _name = '爬虫状况表'
    _conn_name = 'default'
    id = orm.IntegerType(name='id', comment='主键uid', primary_key=True,length=4,unsigned=True,auto_increase=True)
    spider_name = orm.CharType(name='spider_name', comment='爬虫名称',length=255,varchar=True,blank=False)
    description = orm.CharType(name='description', comment='描述', length=512, varchar=True)
    last_run = orm.DatetimeType(name='last_run',comment='上次运行')
    website = orm.CharType(name='website', comment='爬取的网站', length=255, varchar=True)
    ukey_spider_name_index = orm.UniqueKey(key_name='ukey_spider_name_index',col_name='spider_name')
    #last_error = orm.DatetimeType(name='last_error',comment='上次出错')


if StartCommend.debug() or not DBLOGGER_ENABLE:
    class DBLogger(object):

        @staticmethod
        def log(*args):
            pass
        @staticmethod
        def set(*args,**kwargs):
            pass
        @staticmethod
        def get(task):
            return 'test'
        @staticmethod
        def update_current_url(task,url):
            pass
        @staticmethod
        def start(task):
            pass
else:

    def table_creator(table):
        if not table.status():
            table.create_table()
        return table

    class DBLogger(object):
        _table = table_creator(FatalLog)
        _status_table = table_creator(SpiderPid)
        _instance = INSTANCE_NAME
        _author_info = {}
        _desc_info = {}
        _current_url = {}
        _task_website = {}
        @staticmethod
        def log(task,traceback_str,log_time):
            url = DBLogger._current_url.get(task,'')
            new_log_obj = FatalLog()
            new_log_obj.instance = DBLogger._instance
            new_log_obj.task_name = task
            new_log_obj.traceback_str = traceback_str
            new_log_obj.log_time = log_time
            new_log_obj.author = DBLogger.get(task)
            new_log_obj.related_url=url
            new_log_obj.save()

        @staticmethod
        def update_current_url(task, url):
            DBLogger._current_url[task]=url

        @staticmethod
        def set(task,author=None,desc=None,website=None):
            if author is None:
                author = DEFAULT_AUTHOR
            if desc is None:
                desc = u'需要输入说明'
            else:
                # 将desc转换为unicode
                if not isinstance(desc,unicode):
                    desc = desc.decode('utf-8')
            DBLogger._task_website[task] = website
            DBLogger._author_info[task] = author
            DBLogger._desc_info[task] = desc

        @staticmethod
        def get(task):
            return DBLogger._author_info[task]

        @staticmethod
        def start(task):
            pid_obj = DBLogger._status_table.all_objects().filter(spider_name=task).select()
            task_desc = DBLogger._desc_info[task]
            website = DBLogger._task_website[task]
            if pid_obj is None:
                pid_obj = DBLogger._status_table()
                pid_obj.spider_name = task
                pid_obj.last_run = datetime.now()
                pid_obj.description = task_desc
                if website:
                    pid_obj.website = website
                pid_obj.save()
            else:
                pid_obj.last_run = datetime.now()
                if task_desc:
                    pid_obj.description = task_desc
                if website:
                    pid_obj.website = website
                pid_obj.save()



def core_log_imp(string):
    print string

def core_fatal_imp(string):
    sys.stderr.write(string)

def now_log_time():
    return datetime.now().strftime(TIME_FORMAT)


class CoreLogger(object):
    """
    生成如下格式log
    [E task time] message
    [I task time] message
    [W task time] message
    """
    error_partten = '[E {0} {1}] {2}'
    info_partten= '[I {0} {1}] {2}'
    warning_partten = '[W {0} {1}] {2}'

    @staticmethod
    def log(task,message):
        log_str = CoreLogger.info_partten.format(task, now_log_time(), message)
        core_log_imp(log_str)

    @staticmethod
    def _error(task,message,error, logtime):
        error_str = '%s:%s' % (error.__class__.__name__, error.message) if error else ''
        real_message = '%s %s' % (message if message else '', error_str)
        return CoreLogger.error_partten.format(task, logtime.strftime(TIME_FORMAT)
, real_message)

    @staticmethod
    def error(task,message=None,error=None):
        core_log_imp(CoreLogger._error(task,message,error,datetime.now()))

    @staticmethod
    def warning(task,message):
        log_str = CoreLogger.warning_partten.format(task, now_log_time(), message)
        core_log_imp(log_str)

    @staticmethod
    def fatal(task, traceback_str,message=None,error=None,dblog=False):
        log_time = datetime.now()
        log_str = CoreLogger._error(task,message,error,log_time)
        core_log_imp(log_str)
        core_fatal_imp('\n'.join([log_str,traceback_str]))
        if dblog is True:
            try:
                DBLogger.log(task,traceback_str,log_time)
            except Exception as e:
                CoreLogger.error('DBLogging' ,'%s:%s' % (e.__class__.__name__, e.message))
