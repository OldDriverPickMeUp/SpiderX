#coding=utf-8

import base64,threading,requests,urlparse,time
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from core.error import CoreError
from heapq import heappush,heappop
from componet.urlfetcher.filter import IntervalFilter
from componet.urlfetcher.proxy import register,BaseProxy


# 注册阿布云动态代理
# 默认调用，且使用key dynamic 也可以调用
@register('default','dynamic')
class DynamicAbuyunProxy(BaseProxy):
    """
    阿布云动态代理
    限制最大请求速率为0.2秒一次
    增加过滤器来实现最大速率限制
    header 'Proxy-Authorization'
    """
    __proxies = {
        "http": "http://proxy.abuyun.com:9020",
        "https": "http://proxy.abuyun.com:9020"
    }
    __add_header = {'Proxy-Authorization': 'Basic ' + base64.b64encode('your secert code')}
    __filter = IntervalFilter(1)

    @staticmethod
    def build(fetcher):
        """
        this method will be called in fetcher object build its fetch method 
        """
        # add authorization section for this request
        fetcher.header.update(DynamicAbuyunProxy.__add_header)

        # set proxies paras for this request
        fetcher.proxy = DynamicAbuyunProxy.__proxies

        # if this fetcher does not have an filter object
        # an default filter will set to it
        if fetcher.filter is None:
            fetcher.filter = DynamicAbuyunProxy.__filter


# 注册阿布云代理，使用key can_redirect 调用
# fetch.use_proxy(key)
@register('can_redirect')
class CanRedirectAbuyunProxy(BaseProxy):
    """
    可以使用requests自带 重定向的代理
    """
    __proxies = {
        "http": "http://your-user-name:your-passwd@proxy.abuyun.com:9020",
        "https": "https://your-user-name:your-passwd@proxy.abuyun.com:9020"
    }
    __filter = IntervalFilter(1)

    @staticmethod
    def build(fetcher):
        # set proxies paras for this request
        fetcher.proxy = CanRedirectAbuyunProxy.__proxies

        # if this fetcher does not have an filter object
        # an default filter will set to it
        if fetcher.filter is None:
            fetcher.filter = CanRedirectAbuyunProxy.__filter


# 注册动态代理池 为key fetch_proxy的调用
# 使用方式 fetcher.use_proxy('fetch_proxy')
@register('fetch_proxy')
class FetchProxy(BaseProxy):
    """
    从http://www.xicidaili.com/nn/爬取的代理
    """
    __filter = IntervalFilter(1)

    @staticmethod
    def build(fetcher):
        url = fetcher.url
        if url is None:
            raise CoreError('this kind of proxy must have a url before set proxy')
        parsed = urlparse.urlparse(url)
        if parsed.scheme == 'https':
            fetcher.proxy = ProxyPool.get_https()
            fetcher.on_finish = lambda obj=ProxyPool, ip=fetcher.proxy['https']: obj.give_back_https(ip)
            fetcher.on_retry = lambda x=fetcher:FetchProxy.build(fetcher)
        elif parsed.scheme == 'http':
            fetcher.proxy = ProxyPool.get_http()
            fetcher.on_finish = lambda obj=ProxyPool, ip=fetcher.proxy['http']: obj.give_back_http(ip)
            fetcher.on_retry = lambda x=fetcher: FetchProxy.build(fetcher)
        else:
            raise CoreError('fetch url error:%s' % url)
        if fetcher.filter is None:
            fetcher.filter = FetchProxy.__filter



class ProxyPool:
    """
    首先get代理，会先代理从池里弹出一个代理，
    如果使用结束没有问题再还回池中放在最后，
    如果当前池中没有可用的，那就去爬新的，
    当发现代理失效后，不放回池中
    然后再从池中获取新的ip
    """
    _url_template = 'http://www.xicidaili.com/nn/%s'
    _lock = threading.Lock()
    _http_ip_list = []
    _https_ip_list = []
    _stable_https = []
    _stable_http = []
    _last_info = {}

    @staticmethod
    def get_http():
        ProxyPool._lock.acquire()
        if ProxyPool._stable_http:
            last_use, _ = ProxyPool._stable_http[0]
            if time.time() - last_use < 120:  # 距离上次使用有两分钟
                http_proxy_ip = ProxyPool.get_new_http()
            else:
                _, http_proxy_ip = heappop(ProxyPool._stable_http)
        else:
            http_proxy_ip = ProxyPool.get_new_https()
        ProxyPool._lock.release()
        return {'http': http_proxy_ip}

    @staticmethod
    def get_https():
        ProxyPool._lock.acquire()
        if ProxyPool._stable_https:
            last_use,_ = ProxyPool._stable_https[0]
            if time.time()-last_use<120: #距离上次使用有两分钟
                https_proxy_ip = ProxyPool.get_new_https()
            else:
                _, https_proxy_ip = heappop(ProxyPool._stable_https)
        else:
            https_proxy_ip = ProxyPool.get_new_https()
        ProxyPool._lock.release()
        return {'https':https_proxy_ip}

    @staticmethod
    def get_new_https():
        if ProxyPool._https_ip_list:
            return ProxyPool._https_ip_list.pop(0)
        else:
            ProxyPool.get_proxy_ips()
        if not ProxyPool._https_ip_list:
            raise CoreError('ProxyPool can not get more proxy,somthing may be wrong for fetch ip')
        return ProxyPool._https_ip_list.pop(0)

    @staticmethod
    def get_new_http():
        if ProxyPool._http_ip_list:
            return ProxyPool._http_ip_list.pop(0)
        else:
            ProxyPool.get_proxy_ips()
        if not ProxyPool._http_ip_list:
            raise CoreError('ProxyPool can not get more proxy,somthing may be wrong for fetch ip')
        return ProxyPool._http_ip_list.pop(0)

    @staticmethod
    def give_back_https(ip_info):
        ProxyPool._lock.acquire()
        heappush(ProxyPool._stable_https,(time.time(),ip_info))
        ProxyPool._lock.release()

    @staticmethod
    def give_back_http(ip_info):
        ProxyPool._lock.acquire()
        heappush(ProxyPool._stable_http,(time.time(),ip_info))
        ProxyPool._lock.release()

    @staticmethod
    def get_fetch_url():
        last_get = ProxyPool._last_info.get('last_get',None)
        if last_get is not None and isinstance(last_get,datetime):
            if datetime.now() - last_get > timedelta(hours=3):
                # 从第一页开始爬
                ProxyPool._last_info['last_page']=1
                ProxyPool._last_info['last_get'] = datetime.now()
                return ProxyPool._url_template % 1
            else:
                last_page = ProxyPool._last_info.get('last_page')
                if last_page is None:
                    get_page = 1
                else:
                    get_page = last_page + 1
                ProxyPool._last_info['last_page'] = get_page
                ProxyPool._last_info['last_get'] = datetime.now()
                return ProxyPool._url_template % get_page
        else:
            ProxyPool._last_info['last_page'] = 1
            ProxyPool._last_info['last_get'] = datetime.now()
            return ProxyPool._url_template % 1

    @staticmethod
    def get_proxy_ips():
        url = ProxyPool.get_fetch_url()
        web_data = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'})
        soup = BeautifulSoup(web_data.text, 'lxml')
        ips = soup.find_all('tr')
        http_ip_list = []
        https_ip_list = []
        for i in xrange(1,len(ips)):
            ip_info = ips[i]
            tds = ip_info.find_all('td')
            if tds[5].text == 'HTTPS':
                https_ip_list.append(':'.join([tds[1].text, tds[2].text]))
            elif tds[5].text == 'HTTP':
                http_ip_list.append(':'.join([tds[1].text, tds[2].text]))
        ProxyPool._https_ip_list.extend(https_ip_list)
        ProxyPool._http_ip_list.extend(http_ip_list)