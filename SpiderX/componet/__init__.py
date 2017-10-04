#coding=utf-8
from .urlfetcher.constructor import Fetcher
from .userlogger.tasklogger import TaskLogger
from .qiniusave.qiniustore import qiniu_fetch_file,is_url,transform_to_http,qiniu_upload_file,save_pic
from requests.exceptions import Timeout,ConnectionError
from core.corelogger import CoreLogger
from store.tmpfile import SaveFiles


def save_to_qiniu_by_url(url,use_proxy = True,timeout=None):
    if not is_url(url):
        return ''
    new_url = transform_to_http(url)

    fet = Fetcher(new_url).add_header()
    if use_proxy:
        fet.use_proxy()
    if isinstance(timeout,int):
        fet.set_timeout(timeout)
    try:
        responce = fet.get()
        try:
            type_str = responce.headers['Content-Type']
        except KeyError:
            return ''
    except (Timeout,ConnectionError,KeyError) as e:
        CoreLogger.error(error=e,task='save_to_qiniu_by_url')
        return str(url)
    if type_str.startswith('image'):
        return qiniu_upload_file(responce)
    return ''


def save_to_file_by_url(folder_name,save_name,url,use_proxy=True):
    if not is_url(url):
        return False
    new_url = transform_to_http(url)
    fet = Fetcher(new_url).add_header()
    if use_proxy:
        fet.use_proxy()
    responce = fet.safe_get()
    if responce is None:
        return False
    store = SaveFiles(folder_name, save_name)
    store.save(save_pic, responce)
    return True

