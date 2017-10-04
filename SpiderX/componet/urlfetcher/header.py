#coding=utf-8

import random
from core.error import CoreError
from core.corelogger import CoreLogger

ALL_HEADERS = {}


def get_header(key):
    if key is None:
        return random.choice(ALL_HEADERS.values()).copy()
    else:
        header = ALL_HEADERS.get(key)
        if header is None:
            raise CoreError('No matched header key %s' % key)
        return header.copy()


def register(key,header):
    CoreLogger.log('header','|--> header type %s loaded' % key)
    ALL_HEADERS[key]=header