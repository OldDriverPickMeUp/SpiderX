#coding=utf-8

import traceback,sys
from datetime import datetime

from dao.daofactory import DaoFactory
from .error import DBQueryError,CoreError,UserError

class _CommonSection(object):
    def __init__(self,name,type):
        self.name = name
        self.type = type

    def on(self,evt):
        func = getattr(self,evt,None)
        if func is None:
            return ()
        else:
            return func()


class _CommonCreate(_CommonSection):
    def insert(self):
        return (self.name,datetime.now())

class _CommonUpdate(_CommonSection):
    def update(self):
        return (self.name,datetime.now())
    def insert(self):
        return (self.name,datetime.now())

class BaseModel(object):
    _fields=[]
    _desc = {}
    _table = None
    _name = None
    _res_field = None
    _uid = None
    _type = {}
    _index = []
    _common_fields=[]
    _conn_name = None
    #_right = assert len(_fields)==len(_desc)

    @classmethod
    def connect(cls):
        return DaoFactory.connect(cls._conn_name)

    @classmethod
    def query(cls,sql,value=[]):
        conn = cls.connect()
        cursor = conn.cursor()
        try:
            if value:
                cursor.execute(sql,value)
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
    def submit(cls,sql,value=[]):
        conn = cls.connect()
        cursor = conn.cursor()
        try:
            if value:
                cursor.execute(sql, value)
            else:
                cursor.execute(sql)
            cursor.close()
            conn.close()
        except:
            cursor.close()
            conn.close()
            exc_type, exc_value, _ = sys.exc_info()
            raise exc_type(exc_value)

    @classmethod
    def build(cls):
        # 按照field来build
        # type映射了所有field
        build_items = []
        # 先添加注释这里会重复做，未来可能需要重构逻辑
        for key in cls._type.keys():
            cls._type[key].set_comment(cls._desc[key])
        for col_name in cls._fields:
            build_items.append(' '.join([col_name,cls._type[col_name].build()]))
        # 增加common fields
        for each_section in cls._common_fields:
            build_items.append(' '.join([each_section.name,each_section.type.build()]))
        #挨个创建index
        for each_index in cls._index:
            build_items.append(each_index.build())
        create_sql = "CREATE TABLE %s ( %s ) comment='%s';"
        return create_sql % (cls._table,','.join(build_items),cls._name)

    @classmethod
    def remove(cls,uid = None,where = {}):
        if uid is None:
            cls._valid(where)
            where_data = where
        else:
            where_data = {cls._uid:uid}
        if not isinstance(where_data,dict):
            raise Exception('input error')
        sql  = 'DELETE FROM %s WHERE %s;'
        where_fields = where_data.keys()
        where_values = [where_data[n] for n in where_fields]
        where_clause = ' AND '.join(['='.join([n,'%s'])for n in where_fields])
        execute_sql = sql % (cls._table,where_clause)

        cls.submit(execute_sql,where_values)


    @classmethod
    def remove_many_by_id(cls, uid=[]):
        if not isinstance(uid,list):
            raise Exception('error input')
        if len(uid)==0:
            return
        sql = 'DELETE FROM %s WHERE %s IN (%s);'
        in_claues = ','.join(['%s']*len(uid))
        execute_sql = sql % (cls._table, cls._uid,in_claues)

        cls.submit(execute_sql,uid)

    @classmethod
    def update(cls,uid = None,where={},what={}):
        if uid is None:
            cls._valid(where)
            where_data = where
        else:
            where_data = {cls._uid: uid}
        if not isinstance(where_data, dict):
            raise Exception('input error')

        where_fields = where_data.keys()
        where_values = [where_data[n] for n in where_fields]
        where_clause = ' AND '.join(['='.join([n, '%s']) for n in where_fields])

        cls._valid(what)
        what_fields = what.keys()
        what_values = [what[n] for n in what_fields]

        common_data = []
        for n in cls._common_fields:
            common_tmp = n.on('update')
            if common_tmp:
                common_data.append(common_tmp)
        for each_common in common_data:
            what_fields.append(each_common[0])
            what_values.append(each_common[1])

        what_clause = ','.join(['='.join([n, '%s']) for n in what_fields])

        execute_sql = 'UPDATE %s SET %s WHERE %s;' % (cls._table,what_clause,where_clause)

        values = what_values
        values.extend(where_values)
        cls.submit(execute_sql,values)

    @classmethod
    def drop_table(cls):
        # TODO 增加删除表功能
        raise NotImplementedError


    @classmethod
    def insert_many(cls,data):
        # 第一步检查有没有错误的字段
        if isinstance(data,list):
            for each_data in data:
                cls._valid(each_data)
            insert_data = data
        else:
            cls._valid(data)
            insert_data = [data]

        # 准备插入表
        sql = 'INSERT INTO %s (%s) VALUES %s;'
        fields = []
        value_list = []
        for n in insert_data[0].keys():
            fields.append(n)
        for each_data in insert_data:
            tmp = [each_data[n] for n in fields]
            value_list.append(tmp)
        # 增加common数据
        common_data = []
        for n in cls._common_fields:
            common_tmp = n.on('insert')
            if common_tmp:
                common_data.append(common_tmp)
        common_add = []
        for each_common in common_data:
            fields.append(each_common[0])
            common_add.append(each_common[1])
        values = []
        symbols_num = len(fields)

        single_symbol='({0})'.format(','.join(['%s'] * symbols_num))
        for each_value in value_list:
            values.extend(each_value)
            values.extend(common_add)

        execute_sql = sql % (cls._table,','.join(fields),','.join([single_symbol]*len(insert_data)))

        cls.submit(execute_sql,values)

    @classmethod
    def replace(cls,data):
        # 第一步检查有没有错误的字段
        cls._valid(data)
        # 准备插入表
        sql = 'REPLACE INTO %s (%s) VALUES (%s);'
        fields = []
        values = []
        for n in data.keys():
            fields.append(n)
            values.append(data[n])

        # 增加common数据
        common_data = []
        for n in cls._common_fields:
            common_tmp = n.on('insert')
            if common_tmp:
                common_data.append(common_tmp)
        for each_common in common_data:
            fields.append(each_common[0])
            values.append(each_common[1])

        execute_sql = sql % (cls._table, ','.join(fields), ','.join(['%s'] * len(fields)))

        cls.submit(execute_sql,values)

    @classmethod
    def insert(cls, data):
        # 第一步检查有没有错误的字段
        cls._valid(data)

        # 准备插入表
        sql = 'INSERT INTO %s (%s) VALUES (%s);'
        fields = []
        values = []
        for n in data.keys():
            fields.append(n)
            values.append(data[n])
        # 增加common数据
        common_data = []
        for n in cls._common_fields:
            common_tmp = n.on('insert')
            if common_tmp:
                common_data.append(common_tmp)
        for each_common in common_data:
            fields.append(each_common[0])
            values.append(each_common[1])

        execute_sql = sql % (cls._table, ','.join(fields), ','.join(['%s'] * len(fields)))

        cls.submit(execute_sql,values)


    @classmethod
    def insert_nx_update_ex(cls, data, ukeyname=None):
        # 第一步检查有没有错误的字段
        cls._valid(data)
        fields = []
        values = []
        for n in data.keys():
            fields.append(n)
            values.append(data[n])

        # 增加common数据
        common_data = []
        for n in cls._common_fields:
            common_tmp = n.on('insert')
            if common_tmp:
                common_data.append(common_tmp)
        for each_common in common_data:
            fields.append(each_common[0])
            values.append(each_common[1])


        # 为了不让主键自增应该先查询uniquekey
        # 如果查到数据 就update
        # 查不到用insert
        # 获取表的ukey
        ukey_collist = None
        if ukeyname is None:
            # 查找 ukey
            for n in cls._index:
                if isinstance(n,UniqueKey):
                    ukey_collist = n.kwargs['col_name']
                    if not isinstance(ukey_collist,list):
                        ukey_collist=[ukey_collist]
                    break
        else:
            for n in cls._index:
                if isinstance(n,UniqueKey):
                    name = n.kwargs['key_name']
                    if ukeyname == name:
                        ukey_collist=n.kwargs['col_name']
                        if not isinstance(ukey_collist,list):
                            ukey_collist=[ukey_collist]
                        break
        if ukey_collist is None:
            raise UserError('error input ukey name %s' % ukeyname)
        # 找到合适的ukey
        # 然后获取ukey的值查询
        ukey_data = {}
        for n in ukey_collist:
            tmp = data.get(n)
            if tmp is None:
                raise UserError('%s is not found in input data' % n)
            ukey_data[n] = tmp
        obj = cls.select_eq_filter(**ukey_data)
        if obj:
            cls.update(what=data,where=ukey_data)
        else:
            cls.insert(data=data)

    @classmethod
    def _valid(cls,data):
        if not isinstance(data,dict):
            raise CoreError('data type error')
        for n in data.keys():
            if n not in cls._fields:
                raise CoreError('unexcept key %s' % n)
            if n == cls._uid:
                raise CoreError('can not asign main key')


    @classmethod
    def post_process(cls):
        # TODO 一些后处理
        raise NotImplementedError

    @classmethod
    def status(cls):
        execute_sql = "SELECT table_name FROM information_schema.TABLES WHERE table_name = '%s' AND table_schema='%s';" \
                      % (cls._table,DaoFactory.get_conf(cls._conn_name)['db'])

        res = cls.query(execute_sql)

        if len(res)>0:
            return True
        else:
            return False

    @classmethod
    def show_create_table(cls,build_text):
        show_str = build_text.replace(',',',\n')
        print show_str

    @classmethod
    def create_table(cls):
        build_text = cls.build()
        cls.submit(build_text)

    @classmethod
    def select_all(cls):
        sql = 'SELECT %s FROM %s ORDER BY %s'
        execute_sql = sql % (','.join(cls._fields),cls._table,cls._uid)
        res = cls.query(execute_sql)
        object = []
        for n in res:
            object.append(cls(dict(zip(cls._fields, n))))
        return object

    @classmethod
    def select_eq_filter(cls,**kwargs):
        keys = []
        values = []
        for key,value in kwargs.items():
            keys.append(key)
            values.append(value)
        where_clause = ' AND '.join(['='.join([n,'%s']) for n in keys])
        sql = 'SELECT %s FROM %s %s ORDER BY %s'
        execute_sql = sql % (','.join(cls._fields),cls._table,('WHERE %s' % where_clause) if where_clause else '' , cls._uid)
        res = cls.query(execute_sql,values)
        object = []
        for n in res:
            object.append(cls(dict(zip(cls._fields, n))))
        return object

    @classmethod
    def select_like_filter(cls, **kwargs):
        keys = []
        values = []
        for key, value in kwargs.items():
            keys.append(key)
            values.append(value.join(['%']*2))
        where_clause = ' AND '.join([' LIKE '.join([n, '%s']) for n in keys])
        sql = 'SELECT %s FROM %s %s ORDER BY %s'
        execute_sql = sql % (
        ','.join(cls._fields), cls._table, ('WHERE %s' % where_clause) if where_clause else '', cls._uid)
        #print execute_sql
        res = cls.query(execute_sql, values)
        object = []
        for n in res:
            object.append(cls(dict(zip(cls._fields, n))))
        return object

    @classmethod
    def select_custom_filter(cls, **kwargs):
        keys = []
        patterns = []
        for key, pattern in kwargs.items():
            keys.append(key)
            patterns.append(pattern)
        where_clause = ' AND '.join([ pa.format(ke) for ke,pa in zip(keys,patterns)])
        sql = 'SELECT %s FROM %s %s ORDER BY %s'
        execute_sql = sql % (
            ','.join(cls._fields), cls._table, ('WHERE %s' % where_clause) if where_clause else '', cls._uid)
        res = cls.query(execute_sql)
        object = []
        for n in res:
            object.append(cls(dict(zip(cls._fields, n))))
        return object

    @classmethod
    def select_custom_where(cls, where_clause):
        sql = 'SELECT %s FROM %s %s ORDER BY %s'
        execute_sql = sql % (
            ','.join(cls._fields), cls._table, where_clause, cls._uid)
        res = cls.query(execute_sql)
        object = []
        for n in res:
            object.append(cls(dict(zip(cls._fields, n))))
        return object



    # 下面是基本对象的支持
    def __init__(self,datamap):
        self.datamap = datamap

    def __getitem__(self, item):
        return self.datamap.__getitem__(item)

    def __setitem__(self, key, value):
        return self.datamap.__setitem__(key,value)




class Const:
    utf8_unicode_ci = 'utf8_unicode_ci'
    utf8_chinese_ci = 'utf8_chinese_ci'


class _BaseTableType(object):
    _sql = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def build(self):
        raise NotImplementedError

class _BaseDataType(_BaseTableType):

    def build(self):
        out_char = self.parse_type()
        out_char.extend(self.parse_common())
        return ' '.join(out_char)

    def verify(self):
        raise NotImplementedError

    def parse_common(self):
        add_str = []
        unsigned = self.kwargs.get('unsigned')
        if unsigned is True:
            add_str.append('UNSIGNED')
        not_null = self.kwargs.get('not_null')
        collate = self.kwargs.get('collate')
        if collate:
            add_str.append('COLLATE %s' % collate)
        if not_null is True:
            add_str.append('NOT NULL')
        default = self.kwargs.get('default')
        if default:
            add_str.append('DEFAULT %s' % default)
        auto_increment = self.kwargs.get('auto_increment')
        if auto_increment is True:
            add_str.append('AUTO_INCREMENT')
        comment = self.kwargs.get('comment')
        if comment:
            add_str.append("COMMENT '%s'" % comment)
        return add_str

    def parse_type(self):
        length = self.kwargs.get('length')
        if length:
            type_str = self._sql % length
        else:
            type_str = self._sql
        return [type_str]

    def set_comment(self,comment):
        self.kwargs['comment'] = comment


class Decimal(_BaseDataType):
    _sql = 'DECIMAL(%s,%s)'

    def parse_type(self):
        length = self.kwargs.get('length')
        float_length = self.kwargs.get('float_length')
        if length and float_length:
            type_str = self._sql % (length,float_length)
        else:
            type_str = self._sql
        return [type_str]


class Varchar(_BaseDataType):
    _sql = 'VARCHAR(%s)'

class Char(_BaseDataType):
    _sql = 'CHAR(%s)'


class Bigint(_BaseDataType):
    _sql = 'BIGINT(%s)'

class Int(_BaseDataType):
    _sql = 'INT(%s)'

class TimeStamp(_BaseDataType):
    _sql = 'timestamp'


class _BaseKey(_BaseTableType):

    def build(self):
        self.verify()
        key_name = self.kwargs.get('key_name')
        col_name = self.kwargs.get('col_name')
        add_str = []
        if key_name is not None:
            add_str.append(key_name)
        if col_name is not None:
            if isinstance(col_name,list):
                add_str.append(','.join(col_name))
            else:
                add_str.append(col_name)
        return self._sql.format(*add_str)

    def verify(self):
        raise NotImplementedError


class PrimaryKey(_BaseKey):
    _sql = 'PRIMARY KEY ({0})'
    def verify(self):
        if 'key_name' in self.kwargs or 'col_name' not in self.kwargs:
            raise Exception('error input')


class Key(_BaseKey):
    _sql = 'KEY {0} ({1})'
    def verify(self):
        if 'key_name' not in self.kwargs or 'col_name' not in self.kwargs:
            raise Exception('error input')

class UniqueKey(_BaseKey):
    _sql = 'UNIQUE KEY {0} ({1})'
    def verify(self):
        if 'key_name' not in self.kwargs or 'col_name' not in self.kwargs:
            raise Exception('error input')