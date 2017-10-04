#coding=utf-8

import weakref,urlparse
from core.error import CoreError
from core.corelogger import CoreLogger,DBLogger
from utils.taskfinder import find_taskname
from requests.exceptions import Timeout,ConnectionError,RequestException
from implement import get_implement
from .implement import BaseImplement
from .header import get_header
from .proxy import get_proxy
from .cookie import get_cookie
from .filter import DelayFilter
import requests


def is_url(url):
    if url.find('http')==-1:
        return False
    else:
        return True

class Fetcher(object):
    #__imp = None
    __hooks = {}

    def __init__(self, url=None,method = 'GET', **kwargs):
        self.taskname = find_taskname()
        self._retry_time = 5
        self.redirect_time = 0
        self._max_redirect = 3
        self.url = url
        self.options = kwargs
        self.has_header = False
        self.header = {}
        self.has_proxy = False
        self.proxy = {}
        self.has_cookie = False
        self.cookie = {}
        self.filter = None
        self.method = method
        self._param = {}
        self._tuple_param = None
        self.coding = 'utf-8'
        self.builded = False
        self.session = None
        self.call_hook('on_build')
        self.on_finish = None
        self.on_retry = None
        self._implement_name = None
        self._sleep_time = None

    def add_header(self, key=None,**kwargs):

        if key is not None:
            self.options['header'] = key
        if self.options.get('header_add') and kwargs:
            self.options['header_add'].update(kwargs)
        else:
            self.options['header_add'] = kwargs
        self.has_header = True
        return self

    def set_timeout(self,timeout):
        self.options['timeout'] =timeout
        return self

    def use_proxy(self, key=None):
        self.options['proxy'] = key
        self.has_proxy = True
        return self

    def add_cookies(self, key=None, **kwargs):
        self.options['cookie'] = key
        self.options['cookie_add'] = kwargs
        self.has_cookie = True
        return self

    def add_params(self,**kwargs):
        if not kwargs:
            raise CoreError('must add something')
        self._param.update(kwargs)
        return self

    def add_tuple_params(self,param_tuple):
        if not param_tuple:
            raise CoreError('must add something')
        self._tuple_param = param_tuple
        return self

    def set_filter(self, delay):
        self.filter = DelayFilter(delay)
        return self

    def set_sleep(self, sleep_time):
        # 在使用selenium 加载后，可能需要等待一段时间，等js加载后才行能获取sourcepage
        # 需要检查sleep_time,不能打于timeout
        self._sleep_time = sleep_time
        return self

    def encoding(self,coding):
        self.coding = coding
        return self

    def retry(self,times):
        self._retry_time = times
        return self

    def _build(self):
        if self.has_header:
            self.header = get_header(self.options.get('header'))
            self.header.update(self.options['header_add'])
        if self.has_proxy:
            proxy_cls = get_proxy(self.options['proxy'])
            proxy_cls.build(self)
        if self.has_cookie:
            self.cookie = get_cookie(self.options['cookie'])
            self.cookie.update(self.options['cookie_add'])
        param = {}
        if self.header:
            param['headers'] = self.header
        if self.proxy:
            param['proxies'] = self.proxy
        if self.cookie:
            param['cookies'] = self.cookie

        if self._tuple_param:
            param['data'] = self._tuple_param
        elif self._param:
            param['data'] = self._param
        self.param = param
        self.builded = True

    def get(self,url=None):
        if self.session is None:
            # 重定向使用同一个session
            self.session = requests.Session()
        if url:
            self.url = url
        elif not self.url:
            raise CoreError('must set url before get the url')
        self._build()
        _implement = get_implement(self._implement_name)
        self.call_hook('on_get')
        DBLogger.update_current_url(self.taskname,self.url)
        tmp_responce = _implement.implement(self)
        if tmp_responce.status_code >=300 and tmp_responce.status_code <400:
            self.redirect_time+=1
            if self.redirect_time>=self._max_redirect:
                CoreLogger.error('get-redirecting','redirect reach max with %s ,there must be something wrong' % self.url)
                return None
            redirect_url = tmp_responce.headers['Location']
            if not is_url(redirect_url):
                return self.get(urlparse.urljoin(self.url,redirect_url))
            else:
                return self.get(redirect_url)
        return tmp_responce

    def safe_get(self,url=None):
        if url is not None:
            self.url = url
        err_record = []
        for times in range(self._retry_time):
            try:
                responce = self.get()
            except (Timeout, ConnectionError) as e:
                err_record.append('%s:%s' % (e.__class__.__name__,self.param.get('proxies','no proxies')))
                if callable(self.on_retry):
                    self.on_retry()
            else:
                if responce is not None:
                    if responce.status_code < 400:
                        self.finish()
                        return responce
                    err_record.append('%s:%s' % (responce.status_code,responce.url))
                #else:
                    #err_record.append('%s:reach max redirect' % self.url)
        CoreLogger.error('safe_get','||'.join(err_record))
        return None


    def call_hook(self,event):
        hook = self.get_hook(self.taskname,event)
        if hook is not None:
            hook(self)

    def finish(self):
        if callable(self.on_finish):
            self.on_finish()

    @staticmethod
    def get_hook(taskname,event):
        if taskname is None:
            raise CoreError('didn\'t find taskname')
        task_hook = Fetcher.__hooks.get(taskname)
        if task_hook is None:
            return None
        func_ref = task_hook.get(event)
        if func_ref is None:
            return None
        func = func_ref()
        if callable(func):
            return func
        # 删除hook
        del Fetcher.__hooks[taskname]
        CoreLogger.log('get_hook','weak_ref dead lost fetcher hook for task:%s' % taskname)

    def set_implement(self,implement_name):
        self._implement_name = implement_name
        return self

    @staticmethod
    def add_hook(event,func):
        taskname = find_taskname()
        if taskname is None:
            raise CoreError('didn\'t find taskname')
        task_hooks = Fetcher.__hooks.get(taskname)
        if task_hooks is None:
            Fetcher.__hooks[taskname]={}
        Fetcher.__hooks[taskname][event] = (weakref.ref(func))


