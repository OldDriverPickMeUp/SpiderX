#coding=utf-8


import base64,threading,requests,urlparse,time
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from core.error import CoreError
from heapq import heappush,heappop
from .filter import IntervalFilter
from core.corelogger import CoreLogger

_ALL_PROXIES = {}


def register(*args):
    if len(args) == 0:
        raise CoreError('must register a str for proxy class')

    def gen_proxies(class_):
        CoreLogger.log('proxy','|--> %s has been registered as %s' % (class_.__name__,','.join(args)))
        for n in args:
            _ALL_PROXIES[n] = class_
        return class_
    return gen_proxies


def get_proxy(key):
    if key is None:
        return _ALL_PROXIES['default']
    else:
        proxy_cls = _ALL_PROXIES.get(key)
        if proxy_cls is None:
            raise CoreError('No proxy class for key %s' % key)
        return proxy_cls


class BaseProxy(object):
    __proxies = None

    @staticmethod
    def build(fetcher):
        raise NotImplementedError








