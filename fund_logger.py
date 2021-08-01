# -*- coding:utf-8 -*-
import logging
import os.path
import sys
import colorlog

#  black, red, green, yellow, blue, purple, cyan, white
log_colors_config = {
    'DEBUG': 'white',  # cyan white
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'purple',
    'CRITICAL': 'bold_red',
}


class Log(object):

    def __init__(self, file_name=None, log_name=None):
        self.logger = logging.getLogger(file_name)
        self.logger.setLevel(level=logging.INFO)
        self.console_format = colorlog.ColoredFormatter(
            fmt='%(log_color)s[%(asctime)s] %(message)s',
            log_colors=log_colors_config
        )
        self.file_format = logging.Formatter(
            fmt='[%(asctime)s] [%(filename)s] [%(funcName)s] [line:%(lineno)d] %(message)s'
        )
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
