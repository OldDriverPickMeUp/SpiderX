# SpiderX

SpiderX是一个简易的爬虫框架，主要要解决的问题如下:

1. 生产过程中各种爬虫统一管理的问题。
2. 生产过程中爬虫需要资源的分配问题。
3. 对需要爬取数据持续跟踪的问题。

适用环境：
小型项目，非分布式，需持续跟踪，需要全局资源托管

目前应用：
托管近百个爬虫，并稳定运行

# 代码目录结构

> SpideX   根目录  
> |--> component 组件  
> |--> extension 组件扩展  
> |--> core  核心  
> |--> dao  数据库  
> |--> orm  数据对象  
> |--> spider  用户爬虫  
> |--> store  存储模块  
> |--> utils   公共模块  
> settings.py  配置文件  
> startup.py  启动文件   
> config.ini  爬虫调度配置文件

启动：  
```python startup.py``` 调试模式
```python startup.py --type product``` 生产模式
```python startup.py --type debug``` 调试模式

生产模式下，会使用```config.ini```中配置的调度方案。调试模式下配置为debug为True的爬虫将会被直接运行。

# 快速开始

用户代码结构：
> SpideX   根目录   
> |--> spider  用户爬虫  
> ----|---> your_spider 你的爬虫  
> ----|----|---> model.py    数据模型  
> ----|----|---> main.py    任务代码  
> ----|----|---> \_\_init\_\_.py    
> ----|----|---> handlers.py    可选，一般用来放handler类

先配置该爬虫使用的数据表类：
```
#model.py

import orm

@orm.build_model
class KeywordKnowledge(orm.Model):
    _table = 'keyword_knowledge'  #表名
    _name = '关键词知识库'    # 注释名
    _conn_path = ''           # 对应dao里相应的数据库链接名称,可选，是任务db路由的特殊情况
    id = orm.IntegerType(name='id',comment='主键uid',primary_key=True,length=7,unsigned=True,auto_increase=True)
    search_name = orm.CharType(name='search_name',varchar=True,length=50,blank=False,comment='搜索匹配')
    full_keyword = orm.CharType(name='full_keyword',varchar=True,length=255,blank=None,comment='知识全名')
    show_logo = orm.CharType(name='show_logo',varchar=True,length=255,blank=None,comment='关键词logo')
    category_id = orm.IntegerType(name='category_id',length=1,unsigned=True,comment='分类')
    order_weight = orm.IntegerType(name='order_weight',length=4, blank=0, comment='排序权重')
    details = orm.CharType(name='details',length=65532,blank=True,comment='细节')
    key_index_category = orm.Key(key_name='key_index_category',col_name='category_id')
```
再配置爬虫任务本身：
```
#main.py

from core.task import ComplexSpiderTask
from . import handlers
import requests
from componet import Fetcher
from datetime import datetime,timedelta


class ThisNews(ComplexSpiderTask):
    conn_path = 'test'        #  将当前的db操作路由到 名为test的db连接上，会对model.py里面所有的数据表类生效，仅在调试模式下有效
    # debug = True            #  设置调试模式，在使用调试模式时，debug为True，会运行该爬虫
    author = 'Your Name'      #  作者名称，在product模式下，并且使能dblog时，会向记录的数据库中写入要记录的爬虫的作者
    description = '某站点的新闻'    #  爬虫描述，在product模式下，并且使能dblog时，会向配置的数据库里更新该爬虫的描述
    website = '某站点的网页'        #  爬虫站点的url，在product模式下，并且使能dblog时，回想配置的数据库里更新该爬虫站点的url
    
    def initialize(self):
        
        # 下面几行代码，保证了，本爬虫在单次运行中总使用同一个session来访问目标站点
        # 当不需要保持session时，可以注释掉下面几句
        self.session = requests.Session()
        def put_session(instance, *args):
            instance.session = self.session
        self.put_session = put_session
        Fetcher.add_hook('on_build', self.put_session)
        
        # 给爬虫队列里加入第一页的处理对象
        self.put(handlers.ThisNewsHandler(datetime.now()-timedelta(days=1)))
```
编写handlers.py的代码
```
#handlers.py

from core.task import ComplexSpiderHandler
from datetime import datetime,timedelta
from . import model
from componet import TaskLogger,Fetcher
from store.storage import ModelStorage


class ThisNewsHandler(ComplexSpiderHandler):

    _url = 'https://www.ThisNewsHandler.com/'

    def __init__(self,stop_time):
        super(ThisNewsHandler,self).__init__(self._url)
        self.stop_time = stop_time
        # ModelStorage对象接收一个数据表类，和一个唯一标识字段
        # 会以唯一标识字段作为去重的标准
        # 同时还接收一个打log的方法，缺省时不会打印日志
        self.storage = ModelStorage(model.KeywordKnowledge,'full_keyword').set_log_method(self.log_method)
    
    # 设置log方法可以更好的记录爬虫的行为
    @staticmethod
    def log_method(data):
        TaskLogger.log('%s %s saved' % (data['published_at'],data['title']))

    def gen_fetcher(self):
        # 生成一个获取器来获取该网页
        self.fetcher = Fetcher(self.url).add_header()

    def parse(self, responce):
        content = responce.text
        
        # 解析网页
        # ...
        # 找到数据
        each_data={}
        each_data['attr1'] = attr1
        each_data['attr2'] = attr2
        each_data['attr3'] = attr3
        each_data['attr4'] = attr4
        self.storage.push(each_data)
        
        # 这里可以返回一个handler的list 或者 一个handler，将会被插入到队列顶端优先执行
        #return AnotherHandler(**kwargs)   

    def next_handler(self):
        return None
        # 这里是类似实现翻页功能，当本handler执行结束后，任务会调用该函数，获取下一个handler，这里只能返回handler对象
        # return AnotherHandler(**kwargs)
```

# 框架的配置

主要包括:

总体配置 /settings.py

生产模式调度配置 /config.ini

内核配置 /core/const.py 不常变

七牛存储配置 /componet/qiniusave/const.py 不常变

获取器配置 /componet/urlfetcher/const.py 不常变

### 具体说明

主要是配置db和常量：
```
# settings.py
JSON_STORE_DIR ='../SpiderXStore/store/json'      # json文件路径
TMP_FILES_DIR = '../SpiderXStore/store/tmpfiles'  # 临时文件路径

HOT_RENEW = True  # 热更新模式 仅在product下有效，当开启后，会热更新爬虫代码和调度的配置


# 数据库配置
DB_SETTING_DICT={
    "default" : {                 # 数据库连接名，与数据表或者爬虫对应，db操作会路由到这张表
        "type": "mysql",
        "conf": {
            "host": "mysql1@xxx",
            "user": "testuser",
            "pass": "pass",
            "db": "test1",
            "port": 3306,
            "max": 2,             # 最大连接数，超过后会阻塞
            "min": 1
        }
    },
    "test" : {
        "type": "mysql",
        "conf": {
            "host": "mysql2",
            "user": "user2",
            "pass": "pass",
            "db": "test2",
            "port": 3306,
            "max": 6,
            "min": 1
        }
    },
}
```
生产模式下爬虫调度的配置：
```
# config.ini

;[spider:spider1]
;db=test2
;type=cron
;hour=10,16
[spider:spider2]     # section 全部爬虫文件夹目录:爬虫文件夹名称
db=chiduo            # 该爬虫的全局db路由
type=cron            # cron 定时方式
hour=12,18
[spider:spider3]
db=ele
type=cron
hour=4,22
[spider:interval_spider]
db=test
type=interval        # interval 定时方式
minutes=30
```
内核配置：
```
#/core/const.py

import os
TASK_DIR = 'spider'       # 设置 核心扫描任务路径名称
FULL_TASK_DIR = os.path.sep.join([os.getcwd(),TASK_DIR])

TIME_FORMAT = '%Y%m%d-%H:%M:%S'     # 日志打印时间格式

CONFIG_NAME = 'config.ini'      # 生产模式下配置文件名称
TIME_ZONE = 'Asia/Shanghai'     # 时区
INSTANCE_NAME = 'SpiderX_main'  # 实例名称，在product模式下，开启dblog后使用
DEFAULT_AUTHOR = 'WANGBY'       # 默认爬虫作者名称
DBLOGGER_ENABLE = True          # 开启dblogger与否，只有在product模式下有效
```
七牛存储配置：
```
# /componet/qiniusave/const.py

ZONE_NAME = 'your_zone'
# 需要填写你的 Access Key 和 Secret Key
Access_Key = ''
Secret_Key = ''
# 外链接域名
DOMAIN = ''
```
获取器配置:
```
#/componet/urlfetcher/const.py

REQUEST_TIME_OUT = 20   # 默认超时时间
```

# 生产模式和调试模式

生产模式下，用于在服务器上无人值守的情况，调试模式主要用于开发的时候。

在生产模式下会使用config.ini的配置来调度所有爬虫。

在调试模式下会直接运行debug为True的爬虫，全局只能存在一个debug为True的爬虫

# 获取模式

目前支持两种获取模式，一种是使用requests，另一种是使用selenium和Chrome。

如果你正确的安装了seleium和Chrome 59以上的版本，在使用Chrome获取时可以正常获取，当没有正确安装时该爬虫会终止。

在windows模式下会模式下会默认不启用headless模式，
在linux下会自动启动headless模式。

在所有模式下都不开启图片。

使用方法：
```
    def gen_fetcher(self):
        self.fetcher = Fetcher(self.url).set_implement('chrome').set_sleep(5)
```
set_implement方法会制定调用Chrome去加载页面，还需要设定一个延时时间来等待js加载。

# 热更新模式

在生产模式下开启热更新，设置HOT_RENEW为True。

扫描器会定期检查spider文件夹下代码的变动以及config.ini的变动，并重新加载他们，这样可以实现修复另一个爬虫的bug而不影响其他的爬虫。

# 核心core  

核心模块主要提供了调度器（scheduler）、扫描器（scanner）、任务模型（task）。

schedular基于apschedular的blockschedular，使用多线程的方式，每个job同时只能启动一个线程。

### 任务模型

在```/spider/your_task_name/main.py```中继承```/core/task.py```中的```UpdateTask```、```SimpleSpiderTask```和```ComplexSpiderTask```类，扫描器在扫描中就会按照配置将任务注册到调度器中。

UpdateTask，用来处理更新任务，不涉及爬虫队列管理。

SimpleSpiderTask，用来处理相对简单的爬虫任务。

ComplexSpiderTask，用来处理复杂的爬虫任务，有任务处理handler，必须继承于```ComplexSpiderHandler```。

# 组件component

目前组件模块中包含三种组件，分别是url获取器（urlfetcher）、用户日志（userlogger）、和七牛存储（qiniusave）。

#### url获取器

使用如下代码引入url获取器对象  
```
from component import Fetcher  
fet = Fetcher(url,method='GET').add_header(**headers).use_proxy(proxy_name).add_cookies(**cookies)  # 配置url获取器   
response = fet.get()    # 获得url的返回，当发生异常后会异常会被raise给用户   
response = fet.safe_get()  # 获得url的返回，如果发生异常会返回None
```

无论在任何用户代码中使用url获取器时，框架会捕获url获取的行为，来有计划的分配已有的代理，或者说根据配置的域名规则来限制请求的最大速度。

可以使用下面的代码来手动设置请求的延时：
```
fet.set_filter(5)   # 为该url获取器设置一个五秒的延时
``` 

#### 七牛存储

七牛存储主要是为了保存爬取到的静态资源，有两种api，第一种是直接给七牛url由七牛去下载该资源并返回url，另一种是将资源下载到本地，然后再从本地上传到七牛云。第一种方法目前已经被淘汰，由于很多资源也存在反爬策略，会造成任务存在不稳定的可能性。因此只提供第二种方式的api，第二种方法会使用默认代理将资源下载到本地，然后上传。

使用下面的代码调用七牛存储：
```
from component import save_to_qiniu_by_url
new_url = save_to_qiniu_by_url(old_url)
```   

当old_url不是一个合法的url时，函数将返回空字符串。  
当获取失败时，函数会返回old_url并打印一条失败日志。

# 扩展组件

extension 目录下保存组件的扩展代码

#### 扩展代理

引入新的代理：

```
from componet.urlfetcher.filter import IntervalFilter  
from componet.urlfetcher.proxy import register,BaseProxy
@register('can_redirect')
class CanRedirectAbuyunProxy(BaseProxy):
    """
    可以使用requests 重定向的代理
    """
    __proxies = {
        "http": "http://H4QXZ74V2Y56Y2YD:DF57A39B0CC3E55F@proxy.abuyun.com:9020",
        "https": "https://H4QXZ74V2Y56Y2YD:DF57A39B0CC3E55F@proxy.abuyun.com:9020"
    }
    __filter = IntervalFilter(1)

    @staticmethod
    def build(fetcher):
        fetcher.proxy = CanRedirectAbuyunProxy.__proxies
        if fetcher.filter is None:
            fetcher.filter = CanRedirectAbuyunProxy.__filter
```     
 

# 存储模块

目前存储模块提供了两种本地持久化的方法，一种是json文件，另一种是临时文件的方式。

还提供了一个存储器对orm层的接口，可以免除爬虫对orm的访问。

#### json存储

使用下面的代码来使用json存储模块：
```
from store.jsonstore import JsonStore  
a_json_store = JsonStore(filename)  #当没有设置filename时将存储为默认文件   
a_json_store.get(key)  #从存储中获得key，如果没有key返回None   
a_json_store.set(key,object_or_value)  #向存储中存入数据，以key,value的方式，未来可能会支持pickle，目前只支持内置的数据类型，包括字典和列表   
a_json_store.save()   # 保存json文件
```

具体的Json文件保存在与根目录同级的```SpiderXStore/store/json/taskname/filename.json```中，可以在settings.py中配置。

#### tmpfiles临时文件存储

使用下面的代码来使用临时文件存储:
```
from store.tmpfile import TmpFiles  
tmpfile = TmpFiles(filename)  # 创建一个临时存储对象 必须提供filename   
def method(f,data):  
    for each_part in data.content:  
        f.write(each_part)  #构造一个写入方法将内存中的数据写入到文件中  
tmpfile.save(method,data)   #使用给定的方法将临时文件写入硬盘  
do something with tmpfile  
tmpfile.remove()  #从本地硬盘中删除该临时文件  
```

具体临时文件在与根目录同级的```SpiderXStore/store/tmpfiles/taskname/```文件夹下。  
可以在settings.py文件中配置。


#### storage来托管orm

使用下面代码来生成一个存储器对象：
```
from store.storage import ModelStorage

#使用存储器托管一个orm类，使用三个字段作为去重的标准
storage = ModelStorage(AnOrmClass_1,[unique_field_1,unique_field_2,unique_field_3])

#使用存储器托管一个orm类，不使用任何去重策略
storage = ModelStorage(AnOrmClass_2)

#使用存储器托管一个orm类，使用单一字段去重
storage = ModelStorage(AnOrmClass_3,unique_field)

#设置存储器的log方法，会使用该方法来打印日志
storage.set_log_method(log_method)

storage.push(data)     # 使用存储器存储数据，当没有重复正确写入后会打印日志

storage.push(data_list)  # 推入一整组数据

```



# orm数据对象模型

目前的orm非常简陋

设计数据表：
```
import orm

@orm.build_model
class KeywordKnowledge(orm.Model):
    _table = 'keyword_knowledge'  #表名
    _name = '关键词知识库'    # 注释名
    _conn_path = ''           # 对应dao里相应的数据库链接名称,可选，是任务db路由的特殊情况
    id = orm.IntegerType(name='id',comment='主键uid',primary_key=True,length=7,unsigned=True,auto_increase=True)
    search_name = orm.CharType(name='search_name',varchar=True,length=50,blank=False,comment='搜索匹配')
    full_keyword = orm.CharType(name='full_keyword',varchar=True,length=255,blank=None,comment='知识全名')
    show_logo = orm.CharType(name='show_logo',varchar=True,length=255,blank=None,comment='关键词logo')
    category_id = orm.IntegerType(name='category_id',length=1,unsigned=True,comment='分类')
    order_weight = orm.IntegerType(name='order_weight',length=4, blank=0, comment='排序权重')
    details = orm.CharType(name='details',length=65532,blank=True,comment='细节')
    key_index_category = orm.Key(key_name='key_index_category',col_name='category_id')
```
生成数据库中数据表:
```
if not KeywordKnowledge.status():
    KeywordKnowledge.create_table()
print KeywordKnowledge.show_create_table()  #查看建表的sql
```
查询:
```
obj = KeywordKnowledge.all_objects(want_fields).filter(**cond).select()
if obj is None:
    # 没有查到
elif isinstance(obj,list):
    # 查到多个
elif isinstance(obj,KeywordKnowledge):
    # 查到一个
```
写入：
```
new_obj = KeywordKnowledge()
new_obj.search_name = ''
new_obj.save() # 插入新数据
```
更改:
```
obj = KeywordKnowledge.all_objects(want_fields).filter(**cond).select()
if isinstance(obj,KeywordKnowledge):
    obj.search_name = ''
    obj.save() # 更新记录
```
其他的尚不支持














