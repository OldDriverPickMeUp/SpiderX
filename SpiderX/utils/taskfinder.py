#coding=utf-8


import inspect
import os
from core.const import FULL_TASK_DIR


def find_taskname(common_prefix=FULL_TASK_DIR):
    norm_common_prefix = os.path.normpath(common_prefix)
    lastframe = inspect.getouterframes(inspect.currentframe())
    complete = False
    for n in lastframe[2:]:
        call_path = os.path.normpath(n[1])
        if os.path.commonprefix([call_path,norm_common_prefix]) == norm_common_prefix:
            complete=True
            break
    if not complete:
        return None
    common_length = len(common_prefix.split(os.path.sep))
    return call_path.split(os.path.sep)[common_length]



