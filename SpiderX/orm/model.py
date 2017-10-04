#coding=utf-8


from .datatype import BaseDataType
from .indextype import BaseIndexType, _PrimaryKey
from .table import Table
from .sqlgenerator import SelectGenerator


class Model(Table):
    _on_create_field = None
    _on_update_field = None
    _fields = None

    def __init__(self):
        self.datamap = {}
        self.select_generator = None

    def __getitem__(self, item):
        return self.datamap.__getitem__(item)

    def __setitem__(self, key, value):
        return self.datamap.__setitem__(key, value)

    def save(self,by=None):
        """
        by 使用其他的ukey update
        """
        if by:
            # todo 先验证by的合法性
            self.__class__.insert_nx_update_ex(data=self.datamap,where={by:self.datamap[by]})
        elif self._uid and hasattr(self,'uid'):
            self._save_update()
            self.__class__.update(uid=self.uid, what=self.datamap)
        else:
            self._save_create()
            return self.__class__.insert(data=self.datamap)

    def _save_create(self):
        if self._on_create_field:
            setattr(self, self._on_create_field, getattr(self.__class__, self._on_create_field)())
        if self._on_update_field:
            setattr(self, self._on_update_field, getattr(self.__class__, self._on_update_field)())

    def _save_update(self):
        if self._on_update_field:
            setattr(self, self._on_update_field, getattr(self.__class__, self._on_update_field)())

    @classmethod
    def all_objects(cls,*args):
        for n in args:
            if n not in cls._fields:
                raise Exception('%s not in model %s\'s query fields' % (n, cls.__name__))
        if args:
            tmp_fields = list(args)
        else:
            tmp_fields = cls._fields[:]
        if cls._uid is not None:
            tmp_fields.append(cls._uid)
        return SelectGenerator(tmp_fields, cls)

    def update_datamap(self,data):
        for each_key,each_value in data.items():
            if each_key not in self.__class__._fields:
                raise Exception('Unexcepted key %s' % each_key)
            setattr(self,each_key,each_value)
        #self.datamap.update(data)

    def on_create(self):
        self[self._on_create_field] = getattr(self.__class__,self._on_create_field)()

    def on_update(self):
        self[self._on_update_field] = getattr(self.__class__, self._on_update_field)()



def build_model(class_):
    data_info = {}
    data_id_count = []
    key_info = {}
    key_id_count = []
    key_objs=[]
    data_names=[]
    primary_key = None
    for attr_name,attr_obj in vars(class_).items():
        if not attr_name.startswith('_'):
            if hasattr(attr_obj, '__class__') and issubclass(attr_obj.__class__, BaseDataType):
                if attr_name != attr_obj.name:
                    raise Exception('table %s\'s attr %s has a different col name %s' % (class_._table,attr_name,attr_obj.name))
                attr_obj_id = attr_obj.id_count
                data_info[attr_obj_id]=(attr_name, ' '.join([attr_name.join(['`','`']),attr_obj.build()]))
                data_id_count.append(attr_obj_id)
                data_names.append(attr_name)
                if hasattr(attr_obj,'primary_key'):
                    attr_obj.mode = 'r'
                    if primary_key is not None:
                        raise Exception('find primary key %s more than one' % attr_name)
                    primary_key = attr_obj_id
                if hasattr(attr_obj,'auto'):
                    if attr_obj.auto == 'on_create':
                        class_._on_create_field = attr_name
                    elif attr_obj.auto == 'on_update':
                        class_._on_update_field = attr_name

            elif hasattr(attr_obj, '__class__') and issubclass(attr_obj.__class__, BaseIndexType):
                if attr_name != attr_obj.key_name:
                    raise Exception('table %s\'s attr %s has a different key name %s' % (class_._table,attr_name,attr_obj.key_name))
                attr_obj_id = attr_obj.id_count
                key_info[attr_obj_id]=(attr_obj.key_name, attr_obj.build())
                key_id_count.append(attr_obj_id)
                key_objs.append(attr_obj)


    # 验证索引列名
    for each_key in key_objs:
        for each_col_name in each_key.col_name:
            if each_col_name not in data_names:
                raise Exception('%s can\'t be found in table columns' % each_col_name)

    # 开始组装
    data_id_count.sort()
    key_id_count.sort()
    class_._fields = [data_info[each_id][0] for each_id in data_id_count if each_id!=primary_key]

    # 生成建表SQL
    build_items=[data_info[key][1] for key in data_id_count]
    if primary_key is not None:
        class_._uid = data_info[primary_key][0]
        build_items.append(_PrimaryKey(class_._uid).build())
    build_items.extend([key_info[key][1] for key in key_id_count])

    create_sql = "CREATE TABLE %s ( %s ) comment='%s';"
    class_._create_sql = create_sql % (class_._table, ','.join(build_items), class_._name)

    return class_


