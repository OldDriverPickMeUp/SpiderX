#coding=utf-8


class DBQueryError(Exception):
    pass


class CoreError(Exception):
    pass


class UserError(Exception):
    pass

class NotAnError(Exception):
    pass

class SpiderFinish(NotAnError):
    pass
