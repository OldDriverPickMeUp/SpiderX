#coding=utf-8

from core.task import ComplexSpiderHandler
from core.error import UserError
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from . import model
from componet import TaskLogger,Fetcher,save_to_qiniu_by_url
from store.storage import ModelStorage
import urlparse,re,time,json


class TodayHandler(ComplexSpiderHandler):

    _url = 'https://www.producthunt.com/'

    def __init__(self,stop_time):
        super(TodayHandler,self).__init__(self._url)
        self.stop_time = stop_time

        # build a storage object using field pid as an unique field to avoid duplicated data object
        # set an log method for storage object
        self.storage = ModelStorage(model.PostBasics,'pid').set_log_method(self.log_method)

    @staticmethod
    def log_method(data):
        TaskLogger.log('%s %s saved' % (data['published_at'],data['title']))

    def gen_fetcher(self):
        # generate a Fetcher object to fetch the target url
        self.fetcher = Fetcher(self.url).add_header()     # add a browser header for this request

        # add special header content to this Fetcher object
        #self.fetcher = Fetcher(self.url).add_header(
        #        **{'Referer': self.referer, 'X-CSRF-Token': self.csrf_token, 'X-Requested-With': 'XMLHttpRequest'})

        # use default proxy to fetch this url
        #self.fetcher = Fetcher(self.url).use_proxy()


    def parse(self, responce):

        content = responce.text
        soup = BeautifulSoup(content,'lxml')
        ul_container = soup.find_all('ul')[-1]
        all_items = ul_container.find_all('li',recursive=False)
        base_url=responce.url
        for each_item in all_items:
            href = each_item.div.a['href']
            link_obj = urlparse.urlparse(href)
            if link_obj.netloc == '':
                href = urlparse.urljoin(base_url,href)
            logo_div,content_div =  each_item.div.a.find_all('div',recursive=False)
            img_src = logo_div.find('img')['src']
            index = img_src.find('?')
            if index!=-1:
                img_src = img_src[:index]
            title_tag,intro_tag,_ = content_div.find_all('div',recursive=False)
            title = title_tag.get_text(strip=True)
            intro = intro_tag.get_text(strip=True)

            # push data to storage
            each_data={}
            each_data['title'] = title
            each_data['intro'] = intro
            each_data['cover'] = save_to_qiniu_by_url(img_src)
            each_data['published_at'] = datetime.now()
            each_data['pid'] = 'any thing you like'
            each_data['link'] = href
            self.storage.push(each_data)

    def next_handler(self):
        # this method is used to handle next page
        return None
        # deal with next page
        # return NextPageHandler()
