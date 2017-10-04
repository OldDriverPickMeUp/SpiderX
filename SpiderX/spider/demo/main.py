#coding=utf-8

from core.task import ComplexSpiderTask
from . import handlers
import requests
from componet import Fetcher
from datetime import datetime,timedelta


class ProductHunt(ComplexSpiderTask):
    conn_path = 'your_conn'
    #debug = True
    description = 'producthunt spider'
    website = 'https://www.producthunt.com/'

    def initialize(self):

        # 在同一次任务中使用同一个会话
        #self.session = requests.Session()
        #def put_session(instance, *args):
        #    instance.session = self.session
        #self.put_session = put_session
        #Fetcher.add_hook('on_build', self.put_session)

        # put first task hanldler into queue
        self.put(handlers.TodayHandler(datetime.now()-timedelta(days=1)))
