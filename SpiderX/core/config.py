#coding=utf-8

"""
本模块提供配置文件的底层封装
可以实现配置的动态载入，在不停止其他任务的情况下动态更新
将提供collect方法来收集目前所有的配置，生成或更新配置对象
模仿supervisor的配置文件方式
[spider:spidername] 相应爬虫的配置文件
[include] 包含的文件
其他的基本配置
在production模式下通过config模块获取启动配置
提过 get_spider(spidername) 来获取爬虫的配置
"""

import os,threading
from ConfigParser import ConfigParser
from .corelogger import CoreLogger
from .const import CONFIG_NAME

if not os.path.exists(CONFIG_NAME):
    raise Exception('in production mode,config.ini is required')


class GlobalConfig:
    _lock = threading.Lock()
    _instance = None

    @staticmethod
    def instance():
        if GlobalConfig._instance is None:
            GlobalConfig._lock.acquire()
            if GlobalConfig._instance is None:
                GlobalConfig._instance = GlobalConfig(CONFIG_NAME)
            GlobalConfig._lock.release()
        GlobalConfig._instance.refresh()
        return GlobalConfig._instance

    def __init__(self,config_file):
        self.config_file = config_file
        self.config_data = None
        self.mod_time = 0

    def collect(self):
        last_mod=os.path.getmtime(self.config_file)
        config_obj = ConfigParser()
        config_obj.read(self.config_file)
            # 先暂时不考虑include
        all_sections = config_obj.sections()
        spider_data = {}
        for each_section in all_sections:
                # switch each_section
            sp_sec_name = each_section.split(':')
            if len(sp_sec_name)==2 and sp_sec_name[0]=='spider':
                sec_data = dict(config_obj.items(each_section))
                job_type = sec_data['type']
                conn_path = sec_data['db']
                del sec_data['type']
                del sec_data['db']
                if job_type =='interval':
                # 暂时不验证startdate,enddate
                    transform = {'days':lambda x:int(x),
                                 'hours':lambda x:int(x),
                                 'minutes':lambda x:int(x),
                                 'seconds':lambda x:int(x)}
                    for key in sec_data.keys():
                        sec_data[key] = transform[key](sec_data[key])
                elif job_type == 'cron':
                    transform = {'day': lambda x: x,
                                 'hour': lambda x: x,
                                 'minute': lambda x: x,
                                 'second': lambda x: x,
                                 'month': lambda x:x,
                                 'week':lambda x:x,
                                 'day_of_week':lambda x:x}
                    # 不准 start_date,end_date,timezone
                    for key in sec_data.keys():
                        sec_data[key] = transform[key](sec_data[key])
                else:
                    raise Exception('type %s is not support' % job_type)
                spider_data[sp_sec_name[1]] = (last_mod,conn_path,job_type,sec_data)
        self.mod_time=last_mod
        self.config_data = spider_data

    def refresh(self):
        last_mod = os.path.getmtime(self.config_file)
        if self.config_data is None:
            self.collect()
        elif last_mod>self.mod_time:
            self.collect()

    def get_spider(self,spider_name):
        return self.config_data[spider_name]

    def has_spider(self,spider_name):
        return spider_name in self.config_data




