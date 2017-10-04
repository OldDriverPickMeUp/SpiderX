#coding=utf-8
import os
import importlib
from .corelogger import CoreLogger
EXTENSION_FOLDER='extension'
EXTENSION_DIR=os.path.sep.join([os.getcwd(),EXTENSION_FOLDER])


def load_extensions():
    CoreLogger.log('extensions','start loading extensions')
    extension_files = [each for each in os.listdir(EXTENSION_DIR) if not each.startswith('_') and each.endswith('.py')]
    extension_imports = ['.'.join([EXTENSION_FOLDER,each.split('.')[0]])for each in extension_files]
    for each in extension_imports:
        importlib.import_module(each)
    CoreLogger.log('extensions','all extensions loaded')