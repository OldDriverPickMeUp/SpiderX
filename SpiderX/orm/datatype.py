#coding=utf-8

from datetime import datetime
from .filters import OrmFilter

class BaseDataType(object):
    _this_type = None
    _type_sql = None
    _id_count = 0

    def __init__(self, name, comment, mode='rw'):
        self.name = name
        self.comment=comment
        self.options={}
        self.mode = mode
        self.filters = []

    def __get__(self,instance,cls):
        if instance is None:
            return self
        else:
            return instance.datamap.get(self.name)

    def allow_set(self,instance,value):
        instance.datamap[self.name] = value

    def forbid_set(self,instance,value):
        raise Exception('forbiden to write')

    def __set__(self,instance,value):
        if not isinstance(value,self._this_type):
            raise TypeError('Except %s.%s value type %s, now is %s' % (instance.__class__.__name__,self.name,str(self._this_type),type(value)))
        for each_filter in self.filters:
            each_filter(value)
        self.set_item(instance,value)
        #instance.datamap[self.name] = value

    def __delete__(self, instance):
        del instance.datamap[self.name]

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self,value):
        if value in ['rw','wr','RW','WR']:
            self.set_item = self.allow_set
        elif value in ['R','r']:
            self.set_item = self.forbid_set
        else:
            raise Exception('wrong read and write mode %s' % value)
        self._mode = value

    @mode.deleter
    def mode(self):
        raise AttributeError('can\'t delete attr')

    def build(self):
        out_char = [self.parse_type()]
        out_char.extend(self.parse_common())
        return ' '.join(out_char)

    def parse_type(self):
        return self._type_sql.format(**self.options)

    def parse_common(self):
        add_str = []
        unsigned = self.options.get('unsigned')
        if unsigned is True:
            add_str.append('UNSIGNED')
        blank = self.options.get('blank')
        if blank is not True and blank is not None and blank is not False:
            # 实际上只有这种是要推荐的
            if not isinstance(blank, self._this_type):
                raise TypeError('Except blank value %s now is %s' % (self._this_type, blank))
            if isinstance(blank, str):
                default_value = '\'%s\'' % blank
            else:
                default_value = blank
            add_str.append('NOT NULL DEFAULT %s' % default_value)
        elif blank is None or blank is True:
            add_str.append('DEFAULT NULL')
        elif blank is False:
            add_str.append('NOT NULL')
        auto_increment = self.options.get('auto_increase')
        if auto_increment is True:
            add_str.append('AUTO_INCREMENT')
        comment = self.options.get('comment')
        if comment:
            add_str.append("COMMENT '%s'" % comment)
        return add_str

    @staticmethod
    def _get_gen_id():
        BaseDataType._id_count += 1
        return BaseDataType._id_count

    def gather_filter(self):
        blank = self.options.get('blank')
        if blank not in [None,True]:
            self.filters.append(OrmFilter.get('disable_none'))


class IntegerType(BaseDataType):
    _this_type = int
    _type_sql = '{type}({length})'

    # todo 其他种类int以后再加
    def __init__(self,
                 name,
                 length,
                 mode='rw',
                 comment='',
                 auto_increase=False,
                 blank=None,
                 bigint=False,
                 unsigned=False,
                 primary_key=False):
        super(IntegerType, self).__init__(name=name, comment=comment, mode=mode)
        # todo 暂时只验证大类型
        self.options['length']= length
        self.options['comment'] = comment
        self.options['auto_increase'] = auto_increase
        self.options['blank'] = blank
        self.options['unsigned'] = unsigned
        if bigint is True:
            self.options['type'] = 'BIGINT'
        else:
            self.options['type'] = 'INT'
        if primary_key is True:
            self.primary_key = True
            self.options['blank'] = False
        self.id_count = self._get_gen_id()


class DecimalType(BaseDataType):
    _this_type = float
    _type_sql = '{type}({length},{float_length})'

    # todo 其他种类int以后再加
    def __init__(self,
                 name,
                 length,
                 float_length,
                 mode='rw',
                 comment='',
                 auto_increase=False,
                 blank=None,
                 unsigned=False,
                 primary_key=False):
        super(DecimalType, self).__init__(name=name, comment=comment, mode=mode)
        # todo 暂时只验证大类型
        self.options['length']= length
        self.options['comment'] = comment
        self.options['auto_increase'] = auto_increase
        self.options['blank'] = blank
        self.options['unsigned'] = unsigned
        self.options['float_length'] = float_length
        self.options['type'] = 'DECIMAL'
        if primary_key is True:
            self.primary_key = True
            self.options['blank'] = False
        self.id_count = self._get_gen_id()


class CharType(BaseDataType):
    _this_type = (str,unicode)
    _type_sql = '{type}({length})'

    # todo 其他种类int以后再加
    def __init__(self,
                 name,
                 length,
                 mode='rw',
                 comment='',
                 blank=None,
                 varchar=False,
                 primary_key=False):
        super(CharType, self).__init__(name=name, comment=comment, mode=mode)
        # todo 暂时只验证大类型
        self.options['length']= length
        self.options['comment'] = comment
        self.options['blank'] = blank
        if varchar is True:
            self.options['type'] = 'VARCHAR'
        else:
            self.options['type'] = 'CHAR'
        if primary_key is True:
            self.primary_key = True
        self.id_count = self._get_gen_id()


class DatetimeType(BaseDataType):
    _this_type = datetime
    _type_sql = 'TIMESTAMP'

    # todo 其他种类int以后再加
    def __init__(self,
                 name,
                 mode='rw',
                 comment='',
                 blank=True,
                 auto=None):
        super(DatetimeType, self).__init__(name=name, comment=comment, mode=mode)
        self.id_count = self._get_gen_id()
        self.options['comment'] = comment
        if auto in ['on_create','on_update']:
            self.auto=auto
        elif auto is not None:
            raise Exception('auto parameter must be \'on_create\' or \'on_update\'')

    def __call__(self, *args, **kwargs):
        return datetime.now()

