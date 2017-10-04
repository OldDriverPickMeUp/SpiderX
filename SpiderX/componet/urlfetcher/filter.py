#coding=utf-8

import threading
import time

from urlparse import urlparse

from .filter_route_map import FILTER_ROUTE_MAP


class BaseFilter(object):
    def __init__(self):
        self._last_use = time.time()
        self._lock = threading.Lock()

    def filter(self, fetcher):
        self._lock.acquire()
        self._filter(fetcher)
        self._last_use = time.time()
        self._lock.release()

    def _filter(self, fetcher):
        raise NotImplementedError


class IntervalFilter(BaseFilter):
    def __init__(self, interval):
        super(IntervalFilter,self).__init__()
        self._interval = interval

    def _filter(self, fetcher):
        tosleep = self._last_use+self._interval - time.time()
        if tosleep>0:
            time.sleep(tosleep)


class DelayFilter(BaseFilter):
    def __init__(self, delay):
        super(DelayFilter,self).__init__()
        self._delay = delay

    def filter(self, fetcher):
        time.sleep(self._delay)

    def _filter(self, fetcher):
        pass


class DomainRouter(object):
    def __init__(self):
        filter_map = {}
        for key, value in FILTER_ROUTE_MAP.items():
            filter_map[key] = IntervalFilter(**value)
        self._filter_map = filter_map

    def filter(self, fetcher):
        domain = urlparse(fetcher.url).netloc
        filter_obj = self._filter_map.get(domain)
        if filter_obj is None:
            filter_obj = self._filter_map['default']
        filter_obj.filter(fetcher)

GLOBAL_DOMAIN_ROUTER = DomainRouter()
