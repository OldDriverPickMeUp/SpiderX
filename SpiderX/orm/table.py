#coding=utf-8

import sys
from dao.daofactory import DaoFactory


"""
model 直接调用table层方法来兼容以前的代码
model 自己组装sql来查询
model 通过table到达db
table 自己现在不做验证 验证在model里处理
table 不做填充 由model来填充
"""


class Table(object):
    _table = None
    _create_sql = None
    _conn_name = None
    _name = None
    _uid = None
    _fields = None

    @classmethod
    def read(cls):
        return DaoFactory.connect(cls._conn_name)

    @classmethod
    def write(cls):
        return DaoFactory.connect(cls._conn_name)

    @classmethod
    def query(cls, sql, value=[]):
        conn = cls.read()
        cursor = conn.cursor()
        try:
            if value:
                cursor.execute(sql, value)
            else:
                cursor.execute(sql)
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return res
        except:
            cursor.close()
            conn.close()
            exc_type, exc_value, _ = sys.exc_info()
            raise exc_type(exc_value)

    @classmethod
    def submit(cls, sql, value=[]):
        conn = cls.write()
        cursor = conn.cursor()
        try:
            if value:
                cursor.execute(sql, value)
            else:
                cursor.execute(sql)
            last_id = cursor.lastrowid
            cursor.close()
            conn.close()
        except:
            cursor.close()
            conn.close()
            exc_type, exc_value, _ = sys.exc_info()
            raise exc_type(exc_value)
        return last_id

    @classmethod
    def _remove_sql(cls,uid,where):
        if uid is None:
            where_data = where
        else:
            where_data = {cls._uid: uid}
        sql = 'DELETE FROM %s WHERE %s;'
        where_fields = where_data.keys()
        where_values = [where_data[n] for n in where_fields]
        where_clause = ' AND '.join(['='.join([n, '%s']) for n in where_fields])
        execute_sql = sql % (cls._table, where_clause)
        return execute_sql, where_values

    @classmethod
    def remove(cls, uid=None, where={}):
        sql,values = cls._remove_sql(uid,where)
        cls.submit(sql, values)

    @classmethod
    def remove_many_by_id(cls, uid=[]):
        if len(uid) == 0:
            return
        sql = 'DELETE FROM %s WHERE %s IN (%s);'
        in_claues = ','.join(['%s'] * len(uid))
        execute_sql = sql % (cls._table, cls._uid, in_claues)

        cls.submit(execute_sql, uid)

    @classmethod
    def update(cls, uid=None, where={}, what={}):
        if uid is None:
            where_data = where
        else:
            where_data = {cls._uid: uid}

        where_fields = where_data.keys()
        where_values = [where_data[n] for n in where_fields]
        where_clause = ' AND '.join(['='.join([n, '%s']) for n in where_fields])

        what_fields = what.keys()
        what_values = [what[n] for n in what_fields]

        what_clause = ','.join(['='.join([n.join(['`','`']), '%s']) for n in what_fields])

        execute_sql = 'UPDATE %s SET %s WHERE %s;' % (cls._table, what_clause, where_clause)

        values = what_values
        values.extend(where_values)
        cls.submit(execute_sql, values)

    @classmethod
    def _insert_many_sql(cls,data):
        if isinstance(data, list):
            insert_data = data
        else:
            insert_data = [data]
            # 准备插入表
        sql = 'INSERT INTO %s (%s) VALUES %s;'
        fields = []
        value_list = []
        all_keys = insert_data[0].keys()
        for n in all_keys:
            fields.append(n.join(['`','`']))
        for each_data in insert_data:
            tmp = [each_data[n] for n in all_keys]
            value_list.extend(tmp)

        symbols_num = len(fields)

        single_symbol = '({0})'.format(','.join(['%s'] * symbols_num))

        execute_sql = sql % (cls._table, ','.join(fields), ','.join([single_symbol] * len(insert_data)))
        return execute_sql,value_list

    @classmethod
    def insert_many(cls, data):
        sql,values = cls._insert_many_sql(data)
        cls.submit(sql, values)

    @classmethod
    def _insert_sql(cls,data):
        sql = 'INSERT INTO %s (%s) VALUES (%s);'
        fields = []
        values = []
        for n in data.keys():
            fields.append(n.join(['`','`']))
            values.append(data[n])
        execute_sql = sql % (cls._table, ','.join(fields), ','.join(['%s'] * len(fields)))
        return execute_sql,values

    @classmethod
    def insert(cls, data):
        sql, values = cls._insert_sql(data)
        return cls.submit(sql, values)

    @classmethod
    def insert_nx_update_ex(cls, data, where):
        # 第一步检查有没有错误的字段
        fields = []
        values = []
        for n in data.keys():
            fields.append(n)
            values.append(data[n])

        obj = cls.select_eq_filter(**where)
        if obj:
            cls.update(what=data, where=where)
        else:
            cls.insert(data=data)

    @classmethod
    def status(cls):
        execute_sql = "SELECT table_name FROM information_schema.TABLES WHERE table_name = '%s' AND table_schema='%s';" \
                      % (cls._table, DaoFactory.get_conf(cls._conn_name)['db'])

        res = cls.query(execute_sql)

        if len(res) > 0:
            return True
        else:
            return False

    @classmethod
    def show_create_table(cls):
        show_str = cls._create_sql.replace(',', ',\n')
        print show_str

    @classmethod
    def create_table(cls):
        cls.submit(cls._create_sql)

    @classmethod
    def select_all(cls):
        sql = 'SELECT %s FROM %s ORDER BY %s'
        execute_sql = sql % (','.join(cls._fields), cls._table, cls._uid)
        res = cls.query(execute_sql)
        object = []
        for n in res:
            object.append(dict(zip(cls._fields, n)))
        return object

    @classmethod
    def select_eq_filter(cls, **kwargs):
        keys = []
        values = []
        for key, value in kwargs.items():
            keys.append(key)
            values.append(value)
        where_clause = ' AND '.join(['='.join([n, '%s']) for n in keys])
        sql = 'SELECT %s FROM %s %s ORDER BY %s'
        execute_sql = sql % (','.join(cls._fields),
                             cls._table,
                             ('WHERE %s' % where_clause) if where_clause else '',
                             cls._uid)
        res = cls.query(execute_sql, values)
        object = []
        for n in res:
            object.append(dict(zip(cls._fields, n)))
        return object

    @classmethod
    def select_like_filter(cls, **kwargs):
        keys = []
        values = []
        for key, value in kwargs.items():
            keys.append(key)
            values.append(value.join(['%'] * 2))
        where_clause = ' AND '.join([' LIKE '.join([n, '%s']) for n in keys])
        sql = 'SELECT %s FROM %s %s ORDER BY %s'
        execute_sql = sql % (','.join(cls._fields),
                             cls._table,
                             ('WHERE %s' % where_clause) if where_clause else '',
                             cls._uid)
        # print execute_sql
        res = cls.query(execute_sql, values)
        object = []
        for n in res:
            object.append(dict(zip(cls._fields, n)))
        return object

    @classmethod
    def select_custom_filter(cls, **kwargs):
        keys = []
        patterns = []
        for key, pattern in kwargs.items():
            keys.append(key)
            patterns.append(pattern)
        where_clause = ' AND '.join([pa.format(ke) for ke, pa in zip(keys, patterns)])
        sql = 'SELECT %s FROM %s %s ORDER BY %s'
        execute_sql = sql % (','.join(cls._fields),
                             cls._table,
                             ('WHERE %s' % where_clause) if where_clause else '',
                             cls._uid)
        res = cls.query(execute_sql)
        object = []
        for n in res:
            object.append(dict(zip(cls._fields, n)))
        return object

    @classmethod
    def select_custom_where(cls, where_clause):
        sql = 'SELECT %s FROM %s %s ORDER BY %s'
        execute_sql = sql % (','.join(cls._fields),
                             cls._table,
                             where_clause,
                             cls._uid)
        res = cls.query(execute_sql)
        object = []
        for n in res:
            object.append(dict(zip(cls._fields, n)))
        return object
