#coding=utf-8


FILTER_ROUTE_MAP = {
    #'www.tuicool.com': {'interval': 5},
    'default': {'interval': 5}
}


def set_default_interval(time_sec):
    obj = {'interval':time_sec}
    FILTER_ROUTE_MAP['default']=obj


def set_netloc_interval(net_loc,time_sec):
    obj = {'interval':time_sec}
    FILTER_ROUTE_MAP[net_loc] = obj

