#coding=utf-8
import orm


@orm.build_model
class PostBasics(orm.Model):
    _table = 'post_basics'
    _name = '文章基本信息'
    id = orm.IntegerType(name='id', primary_key=True,length=20,unsigned=True,auto_increase=True,blank=False, comment='id')
    pid = orm.CharType(name='pid',varchar=True, length=255, blank=False, comment='uid')
    title = orm.CharType(name='title',varchar=True, length=255,blank=False, comment='标题')
    cover = orm.CharType(name='cover',length=1000, comment='封面')
    published_at = orm.DatetimeType(name='published_at', blank=None, comment='发布于')
    intro = orm.CharType(name='intro',varchar=True, length=1000, comment='文章简介')
    link = orm.CharType(name='link', length=1000, comment='文章链接')
    created_at = orm.DatetimeType(name='created_at', comment='创建时间', auto='on_create')
    updated_at = orm.DatetimeType(name='updated_at', comment='更新事件', auto='on_update')
    post_basics_pid_uindex = orm.Key(key_name='post_basics_pid_uindex', col_name='pid')
