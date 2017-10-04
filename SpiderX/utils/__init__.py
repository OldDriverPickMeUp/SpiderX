#coding=utf-8

from datetime import datetime


def get_today_date():
    return datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)