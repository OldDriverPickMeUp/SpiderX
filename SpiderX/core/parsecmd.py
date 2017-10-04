#coding=utf-8


# 本模块用来解析启动命令来确定正确的启动方式

import sys,argparse


class StartCommend:
    _instance = None

    def __init__(self,args):
        parser = argparse.ArgumentParser()
        parser.add_argument('filename')
        parser.add_argument('--type', help='either product or debug', default='debug',choices=('product','debug'))
        self.args = parser.parse_args(args)

    @staticmethod
    def instance():
        if StartCommend._instance is None:
            StartCommend._instance = StartCommend(sys.argv)
        return StartCommend._instance

    @staticmethod
    def debug():
        if StartCommend.instance().args.type=='debug':
            return True
        else:
            return False

if __name__=='__main__':
    a= StartCommend(['-u','parsecmd.py','--type','product'])
    print a.args
