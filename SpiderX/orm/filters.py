#coding=utf-8

from core.error import CoreError


class OrmFilter(object):
    _filters={}

    @staticmethod
    def register(filter_name):
        def inner_wrap(func):
            OrmFilter._filters[filter_name] = func
            return func
        return inner_wrap

    @staticmethod
    def get(filter_name):
        func = OrmFilter._filters.get(filter_name)
        if func is None:
            raise CoreError('can not find orm filter %s')
        return func


@OrmFilter.register('disable_none')
def disable_none(value):
    if value is None:
        raise CoreError('value except not be None')