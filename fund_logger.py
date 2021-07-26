# -*- coding:utf-8 -*-
import logging
import os
import sys


class Log(object):

    def __init__(self, file_name=None, log_name=None):
        self.logger = logging.getLogger(file_name)
        self.logger.setLevel(level=logging.INFO)
        self.console_format = logging.Formatter(fmt='[%(asctime)s] [%(filename)s] [line:%(lineno)d] [%(levelname)s] %(message)s')
        self.file_format = logging.Formatter(fmt='[%(asctime)s] [%(filename)s] [line:%(lineno)d] [%(levelname)s] %(message)s')
        self.log_dir = os.path.join(sys.path[0], 'logs', log_name)

        if not self.logger.handlers:

            ch = logging.StreamHandler()
            ch.setLevel(level=logging.INFO)
            ch.setFormatter(self.console_format)
            self.logger.addHandler(ch)

            fh = logging.FileHandler(filename=self.log_dir, encoding='utf-8')
            fh.setLevel(level=logging.INFO)
            fh.setFormatter(self.file_format)
            self.logger.addHandler(fh)

    def init_logger(self):
        return self.logger
