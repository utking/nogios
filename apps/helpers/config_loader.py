import os
import glob
from os.path import isfile, isdir
from yaml import load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def load_file(file_path=None):
    config = None
    try:
        config_file = open(file_path, mode='r')
        data = config_file.read()
        config_file.close()
        config = load(data, Loader=Loader)
    except Exception as e:
        print(e)
    return config


class ConfigLoader:

    BASE_PATH = None
    config_files = set()

    def __init__(self, base_path=None):
        self.BASE_PATH = base_path

    def get_config_files(self):
        self.config_files = set()
        self.__get_config_files(self.BASE_PATH)
        return self.config_files

    def __get_config_files(self, search_path=None):
        for filename in glob.glob(os.path.join(search_path, '*')):
            if isdir(filename):
                self.__get_config_files(search_path=filename)
            elif isfile(filename):
                if not (filename.endswith(".yaml") or filename.endswith(".yml")):
                    continue
                self.config_files.add(filename)
