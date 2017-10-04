#coding=utf-8
import threading
from DBUtils.PooledDB import PooledDB
from settings import DB_SETTING_DICT
import pymysql

class DaoFactory(object):
    _pool = {}
    _lock = threading.Lock()

    @staticmethod
    def init(key):
        config = DB_SETTING_DICT.get(key)
        if config is None:
            raise Exception('can not get db info from setting file')
        conf = config['conf']
        DaoFactory._pool[key] = PooledDB(pymysql,host = conf['host'],
                                         port = conf['port'],user = conf['user'],
                                         passwd = conf['pass'],db = conf['db'],
                                         charset = conf.get('charset','utf8mb4'),
                                         maxconnections=conf['max'],blocking=True,
                                         autocommit=True)

    @staticmethod
    def connect(key):
        pool = DaoFactory._pool.get(key)
        if pool is None:
            DaoFactory._lock.acquire()
            if DaoFactory._pool.get(key) is None:
                DaoFactory.init(key)
            DaoFactory._lock.release()
            pool = DaoFactory._pool.get(key)
        return pool.connection(shareable=False)

    @staticmethod
    def get_conf(key):
        config = DB_SETTING_DICT.get(key)
        if config is None:
            raise Exception('cannot find key %s' % key)
        return config.get('conf')

    @staticmethod
    def have_conn(key):
        config = DB_SETTING_DICT.get(key)
        if config is None:
            return False
        return True
