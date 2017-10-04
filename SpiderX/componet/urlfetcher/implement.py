#coding=utf-8


import requests,urllib,urlparse,time
from requests.exceptions import ReadTimeout
from core.corelogger import CoreLogger
from core.error import CoreError
from .const import REQUEST_TIME_OUT
from .filter import GLOBAL_DOMAIN_ROUTER
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from valid_webdriver import DRIVER_STATUS

_ALL_IMPLEMENT = {}


def register(*args):
    if len(args) == 0:
        raise CoreError('must register a str for proxy class')

    def add_implement(class_):
        for n in args:
            _ALL_IMPLEMENT[n] = class_
        return class_
    return add_implement


def get_implement(implement_name):
    if implement_name is None:
        return _ALL_IMPLEMENT['requests']
    imp = _ALL_IMPLEMENT.get(implement_name)
    if imp is None:
        raise CoreError('do not have implement named %s' % implement_name)
    return imp


class BaseImplement(object):
    @staticmethod
    def implement(fetcher):
        raise NotImplementedError


@register('requests')
class FetchImplement(BaseImplement):
    @staticmethod
    def implement(fetcher):
        if hasattr(fetcher.filter, 'filter'):
            fetcher.filter.filter(fetcher)
        else:
            GLOBAL_DOMAIN_ROUTER.filter(fetcher)
        if fetcher.session is not None:
            s = fetcher.session
        else:
            s = requests.Session()
        if fetcher.method == 'GET':
            responce = s.get(fetcher.url, timeout=fetcher.options.get('timeout', REQUEST_TIME_OUT), allow_redirects=False,**fetcher.param)
        elif fetcher.method == 'POST':
            responce = s.post(fetcher.url, timeout=fetcher.options.get('timeout', REQUEST_TIME_OUT), allow_redirects=False,**fetcher.param)
        else:
            raise CoreError('do not have such method:%s' % fetcher.method)
        responce.encoding = fetcher.coding
        return responce


class WebDriverResponce:
    def __init__(self,url,content):
        self.url = url
        self.content = content
        self.text = content
        self.status_code = 200      # selenium 并没有获取请求状态码的api故先全部给200


@register('chrome')
class ChromeImplement(BaseImplement):
    @staticmethod
    def implement(fetcher):
        # 在这里fetcher的配置基本毛用没有
        # 只有超时有用
        # 还需要 把超时的错误封装到requests的超时的错误里，来兼容以前的代码
        # 实际上应该先捕获其内部错误，然后转换成SpiderX的标准错误再抛出，这样就可以没错了

        # 先通过过滤器，保证时间上的限制
        if hasattr(fetcher.filter, 'filter'):
            fetcher.filter.filter(fetcher)
        else:
            GLOBAL_DOMAIN_ROUTER.filter(fetcher)

        timeout = fetcher.options.get('timeout', REQUEST_TIME_OUT)
        #开始调用
        if fetcher.method == 'GET':
            chrome_options = DRIVER_STATUS.get('chrome')
            if chrome_options is None:
                raise CoreError('you must install chrome browser first')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            #driver.set_page_load_timeout(timeout)
            #driver.set_script_timeout(timeout)  # 这两种设置都进行才有效
            driver.implicitly_wait(timeout)
            need_to_sleep = fetcher._sleep_time
            if need_to_sleep is None:
                need_to_sleep = 0
            if need_to_sleep>timeout:
                need_to_sleep = timeout
            # 把请求参数拼进url里
            # get方法
            query = fetcher.param.get('data')
            if query:
                query_str = urllib.urlencode(query)
                url_obj = list(urlparse.urlparse(fetcher.url))
                url_obj[4] = query_str
                url = urlparse.urlunparse(url_obj)
            else:
                url = fetcher.url
            try:
                driver.get(url)
                if int(need_to_sleep)>0:
                    time.sleep(need_to_sleep)
            except TimeoutException:
                driver.close()
                raise requests.Timeout()
            # 需要造一个request的responce的封装。。
            # 实际上需要他们有一个统一的封装
            # 呃 以后再搞吧
            source_page = driver.page_source
            driver.close()
            responce = WebDriverResponce(url,source_page)
        else:
            raise CoreError('not support now')
        return responce


class ChromeSimeResponce:
    def __init__(self, url, sim_webdriver):
        self.url = url
        self.status_code = 200
        self.webdriver = sim_webdriver


@register('chrome_sim')
class ChromeSimImplement(BaseImplement):
    @staticmethod
    def implement(fetcher):
        # 在这里fetcher的配置基本毛用没有
        # 只有超时有用
        # 还需要 把超时的错误封装到requests的超时的错误里，来兼容以前的代码
        # 实际上应该先捕获其内部错误，然后转换成SpiderX的标准错误再抛出，这样就可以没错了

        # 先通过过滤器，保证时间上的限制
        if hasattr(fetcher.filter, 'filter'):
            fetcher.filter.filter(fetcher)
        else:
            GLOBAL_DOMAIN_ROUTER.filter(fetcher)

        timeout = fetcher.options.get('timeout', REQUEST_TIME_OUT)
        #开始调用
        if fetcher.method == 'GET':
            chrome_options = DRIVER_STATUS.get('chrome')
            if chrome_options is None:
                raise CoreError('you must install chrome browser first')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            #driver.set_page_load_timeout(timeout)
            #driver.set_script_timeout(timeout)  # 这两种设置都进行才有效
            driver.implicitly_wait(timeout)
            need_to_sleep = fetcher._sleep_time
            if need_to_sleep is None:
                need_to_sleep = 0
            if need_to_sleep>timeout:
                need_to_sleep = timeout
            # 把请求参数拼进url里
            # get方法
            query = fetcher.param.get('data')
            if query:
                query_str = urllib.urlencode(query)
                url_obj = list(urlparse.urlparse(fetcher.url))
                url_obj[4] = query_str
                url = urlparse.urlunparse(url_obj)
            else:
                url = fetcher.url
            try:
                driver.get(url)
                if int(need_to_sleep)>0:
                    time.sleep(need_to_sleep)
            except TimeoutException:
                driver.close()
                raise requests.Timeout()
            # 需要造一个request的responce的封装。。
            # 实际上需要他们有一个统一的封装
            # 呃 以后再搞吧
            responce = ChromeSimeResponce(url,driver)
        else:
            raise CoreError('not support now')
        return responce



class TestImplement(BaseImplement):
    @staticmethod
    def implement(fetcher):
        if hasattr(fetcher.filter, 'filter'):
            fetcher.filter.filter(fetcher)
        else:
            GLOBAL_DOMAIN_ROUTER.filter(fetcher)
        return 'mamamiya'


class DebugImplement(BaseImplement):
    @staticmethod
    def implement(fetcher):
        s = requests.Session()
        pass

