#coding=utf-8

import platform


def get_current_platform():
    return platform.system()


def is_windows():
    if platform.system() == 'Windows':
        return True
    return False


def is_linux():
    if platform.system() == 'Linux':
        return True
    return False


def is_mac():
    if platform.system() == 'Darwin':
        return True
    return False

