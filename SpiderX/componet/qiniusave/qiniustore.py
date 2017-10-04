#coding=utf-8

import qiniu,urlparse,hashlib,time,os
from core.corelogger import CoreLogger
from store.tmpfile import TmpFiles
from .const import ZONE_NAME,Access_Key,Secret_Key,DOMAIN


def qiniu_fetch_file(purl):
    max_retry = 5

    if not is_url(purl):
        CoreLogger.warning(task='qiniu_fetch',message='input url:%s' % purl)
        return ''
    purl = transform_to_http(purl)
    q = qiniu.Auth(Access_Key, Secret_Key)
    Bucket_path = qiniu.BucketManager(q)
    for n in range(max_retry):
        ret = Bucket_path.fetch(purl, ZONE_NAME)
        if ret is None:
            continue
        elif isinstance(ret,tuple) and ret[0] is None:
            continue
        else:
            key = ret[0]['key']
            url = DOMAIN + str(key)
            obj = urlparse.urlparse(url)
            return obj.geturl()
    else:
        CoreLogger.error(task='qiniu_fetch', message='max retry exceed')
        return purl


def get_hash(byte_stream):
    sha_obj = hashlib.sha256(byte_stream)
    hash_code = qiniu.urlsafe_base64_encode(sha_obj.digest()).replace('=','')
    return hash_code


def is_url(url):
    if url is None:
        return False
    if url.find('http') == -1:
        return False
    return True


def transform_to_http(url):
    obj_res = urlparse.urlparse(url)
    if obj_res.scheme == 'https':
        return url.replace('https','http')
    return url


def save_qiniu(name,img_dir):
    q = qiniu.Auth(Access_Key, Secret_Key)
    bucket_name = ZONE_NAME
    key = name
    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(ZONE_NAME, key, 12000)
    #要上传文件的本地路径
    localfile = os.path.sep.join([img_dir,name])
    ret, info = qiniu.put_file(token, key, localfile)
    assert ret['key'] == key
    assert ret['hash'] == qiniu.etag(localfile)
    return DOMAIN+key


def save_pic(file,responce):
    for chunk in responce.iter_content(chunk_size=1024):
        if chunk:  # filter out keep-alive new chunks
            file.write(chunk)


def qiniu_upload_file(responce):
    file_name = get_hash(responce.content)
    store = TmpFiles(file_name)
    store.save(save_pic, responce)
    try:
        result_url = save_qiniu(file_name,os.path.dirname(store.filename))
    except Exception as e:
        CoreLogger.error(error=e,task='qiniu_upload_file')
        result_url = str(responce.url)
    store.remove()
    return result_url


