#coding=utf-8

import inspect,traceback,requests,weakref
from requests.exceptions import Timeout,ConnectionError
from componet import Fetcher
from .error import SpiderFinish,CoreError
from .corelogger import CoreLogger,DBLogger


class UpdateTask(object):
    _logger = None
    _fatal_logger = None
    _filename = None
    conn_path = None

    @classmethod
    def run(cls):
        CoreLogger.log(task=cls.name,message='start')
        DBLogger.start(cls.name)
        try:
            cls.task()
        except Exception as e:
            CoreLogger.fatal(traceback_str=traceback.format_exc(), error=e, task=cls.name,dblog=True)
        CoreLogger.log(task=cls.name,message='finished')


class SimpleSpiderTask(UpdateTask):
    """
    spider task
    提供了一个简单的单线程的爬虫框架
    """

    @classmethod
    def run(cls):
        CoreLogger.log(task=cls.name, message='start')
        DBLogger.start(cls.name)
        instance = cls()
        try:
            instance.initialize()
            instance.task()
        except Exception as e:
            CoreLogger.fatal(traceback_str=traceback.format_exc(), error=e, task=cls.name,dblog=True)
        CoreLogger.log(task=cls.name, message='finished')

    def __init__(self):
        self.url_list = []

    def initialize(self):
        """
        要在这里设置好初始队列
        :return:
        """
        raise NotImplementedError

    def put(self,fetcher,**kwargs):
        self.url_list.append((fetcher,kwargs))

    def insert(self,fetcher,**kwargs):
        self.url_list.insert(0,(fetcher,kwargs))

    def parse(self, responce,params):
        raise NotImplementedError

    def task(self):
        while True:
            if len(self.url_list) == 0:
                break
            fetcher, params = self.url_list.pop(0)
            try:
                if hasattr(fetcher, 'safe_get'):
                    responce = fetcher.safe_get()
                    if responce is None:
                        self.on_timeout(fetcher, params)
                    else:
                        self.parse(responce, params)
                else:
                    raise CoreError('fetcher do not have attr get')
            except CoreError as e:
                CoreLogger.error(error=e, task=self.name)
                continue
            except SpiderFinish:
                break
        self.onfinish()

    def onfinish(self):
        pass

    def on_timeout(self,fetcher,params):
        CoreLogger.log(message='do nothing on read timeout', task=self.name)


class ComplexSpiderHandler(object):
    _max_retry = 2
    _retry_immediately = False
    _gen_immediately = False
    _session_ref = None
    _default_options = {
        'add_header': True,
        'use_proxy': False
    }

    def __init__(self,url):
        self.retry_times = 0
        self.need_retry = False
        self.options = self._default_options
        self.fetcher = None
        self.url = url

    def set_options(self,**kwargs):
        self.options.update(kwargs)

    def on_timeout(self):
        pass

    def on_bad_responce(self, responce):
        pass

    def parse(self, responce):
        raise NotImplementedError

    def next_handler(self):
        raise NotImplementedError

    def gen_fetcher(self):
        # 在这里生成self.fetcher
        # self.fetcher = Fetcher(self.url).add_header().use_proxy()
        raise NotImplementedError

    def fetch(self):
        if self.fetcher is None:
            self.gen_fetcher()
        session = self.session
        if session is not None:
            self.fetcher.session = session
        return self.fetcher.safe_get()

    @property
    def session(self):
        if self.__class__._session_ref is None:
            return None
        return self.__class__._session_ref()

    @session.setter
    def session(self, value):
        raise AttributeError('can\'t set attr session')

    @session.deleter
    def session(self):
        raise AttributeError('can\'t delete attr session')

    @classmethod
    def set_session_ref(cls,obj):
        if isinstance(obj,requests.Session):
            cls._session_ref = weakref.ref(obj)



class ComplexSpiderTask(UpdateTask):
    """
    complex spider task
    提供了一个稍微复杂的爬虫框架

    start_params 提供了爬虫的控制策略

    hold_session: True 将在整个爬虫生命周期内保持cookie
    还有其他用户扩展的命令模式
    """
    start_params = {}

    @classmethod
    def run(cls):
        CoreLogger.log(task=cls.name, message='start')
        DBLogger.start(cls.name)
        instance = cls(**cls.start_params)
        try:
            instance.initialize()
            # instance._build()
            instance.task()
        except CoreError as e:
            CoreLogger.error(error=e, task=cls.name)
        except Exception as e:
            CoreLogger.fatal(traceback_str=traceback.format_exc(),error=e, task=cls.name,dblog=True)
        CoreLogger.log(task=cls.name, message='finished')

    def __init__(self,**kwargs):
        self.url_list = []
        self.hold_session = kwargs.get('hold_session',False)
        self.options = kwargs
        self.handlers = {}
        self.store={}
        if self.options.get('hold_session') is True:
            self.store['session'] = requests.Session()

    def initialize(self):
        """
        在这里添加handler
        """
        raise NotImplementedError

    def add_handler(self,handler,**build_params):
        if not issubclass(handler,ComplexSpiderHandler):
            raise CoreError('Except a ComplexSpiderHandler type obj')
        if self.options.get('hold_session') is True:
            handler.set_session_ref(self.store['session'])
        self.handlers[handler] = build_params.copy()

    def _put(self,handler_obj,immediately=False):
        if not isinstance(handler_obj,ComplexSpiderHandler):
            raise CoreError('Except a ComplexSpiderHandler type obj')
        if immediately:
            self.url_list.insert(0,handler_obj)
        else:
            self.url_list.append(handler_obj)

    def put(self,handler_obj):
        self._put(handler_obj,False)

    def insert(self,handler_obj):
        self._put(handler_obj,True)

    def _build(self):
        for key, value in self.handlers.items():
            obj = key(**value)
            self._put(obj)

    def task(self):
        while True:
            if len(self.url_list) == 0:
                break
            handler_obj = self.url_list.pop(0)
            #if handler_obj.retry_times>0:
            #    CoreLogger.log(task=self.__class__.__name__,
            #                   message='retry:%s %s' % (handler_obj.retry_times,handler_obj.url))
            try:
                responce = handler_obj.fetch()
                if responce is None:
                    handler_obj.on_bad_responce(responce)
                else:
                    more_handlers = handler_obj.parse(responce)
                    if isinstance(more_handlers,(tuple,list)):
                        for each_handler in more_handlers:
                            if hasattr(each_handler,'_gen_immediately'):
                                self._put(each_handler, each_handler._gen_immediately)
                    elif hasattr(more_handlers,'_gen_immediately'):
                        self._put(more_handlers, more_handlers._gen_immediately)
            #except (Timeout,ConnectionError):
            #    handler_obj.on_timeout()
            #    handler_obj.need_retry = True
            except SpiderFinish:
                break
            # 判断正常结束
            #if handler_obj.need_retry and handler_obj.retry_times < handler_obj._max_retry:
            #    self._put(handler_obj,handler_obj._retry_immediately)
            #    handler_obj.retry_times+=1
            #else:
            #    if handler_obj.retry_times==0:
            next_handler = handler_obj.next_handler()
            if next_handler is not None and isinstance(next_handler,ComplexSpiderHandler):
                self._put(next_handler, next_handler._gen_immediately)
        self.onfinish()

    def onfinish(self):
        pass


