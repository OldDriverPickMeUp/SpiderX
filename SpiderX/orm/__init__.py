#coding=utf-8
from .model import Model,build_model
from .datatype import IntegerType,DatetimeType,CharType,DecimalType
from .indextype import Key,UniqueKey


def create_all(module):
    for key, value in vars(module).items():
        if hasattr(value, '__base__') and value.__base__ is Model:
            if not value.status():
                value.create_table()
                print 'created', key
            #else:
            #    print 'exists',key