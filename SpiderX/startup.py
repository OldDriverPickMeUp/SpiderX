#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf8')
from core.parsecmd import StartCommend
from core.scheduler import TaskScheduler
from core.loader import load_extensions
from settings import HOT_RENEW
import logging

log = logging.getLogger('apscheduler.executors.default')
log.setLevel(logging.ERROR)  # DEBUG

fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
h = logging.StreamHandler()
h.setFormatter(fmt)
log.addHandler(h)

def startup():
    """
    启动过程
    完成扫描过程
    构造任务配置
    将任务加入计划任务
    启动计划任务
    """
    load_extensions()
    if StartCommend.debug():
        from core.scanner import Scaner
        # spelling error don't care that
        Scanner = Scaner
        Scanner.scan()
    else:
        from core.newscanner import Scanner
        Scanner.scan(HOT_RENEW)
        TaskScheduler.scheduler().start()

if __name__=='__main__':
    startup()