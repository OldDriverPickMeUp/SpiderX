#coding=utf-8


class BaseIndexType(object):
    _type_sql = None
    _id_count = 0

    def __init__(self, key_name, col_name):
        if isinstance(col_name,list):
            self.col_name = col_name
        else:
            self.col_name = [col_name]
        self.key_name = key_name
        self.options = {'col': ','.join(self.col_name),
                        'key': key_name}
        self.id_count = self._get_gen_id()

    def __get__(self,instance,cls):
        raise Exception('Index obj is not getatble')

    def __set__(self,instance,value):
        raise Exception('Index obj is not setable')

    def __delete__(self, instance):
        raise Exception('Index obj is not deletable')

    def build(self):
        return self._type_sql.format(**self.options)

    @staticmethod
    def _get_gen_id():
        BaseIndexType._id_count += 1
        return BaseIndexType._id_count


class _PrimaryKey(BaseIndexType):
    _type_sql = 'PRIMARY KEY ({col})'

    def __init__(self,col_name):
        super(_PrimaryKey,self).__init__(key_name=None,col_name=col_name)


class Key(BaseIndexType):
    _type_sql = 'KEY {key} ({col})'


class UniqueKey(BaseIndexType):
    _type_sql = 'UNIQUE KEY {key} ({col})'
