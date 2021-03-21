#!/usr/bin/env python
# _*_coding:utf-8_*_

"""
@Time :     2021/3/14 18:57
@Author:    bian
@File:      logger.py
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def create_logger(path, name='BlueEyes'):
    path = os.path.join(path, 'logs')
    os.makedirs(path, exist_ok=True)
    fmt_console = f'{name} %(asctime)s %(levelname)0.4s %(message)s'
    logging.basicConfig(format=fmt_console, level=logging.INFO, datefmt='%H:%M:%S')
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler(
        os.path.join(path, 'log.txt'), maxBytes=1024 * 1024 * 3, backupCount=15, encoding='utf-8')

    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    fmt = f'{name} %(asctime)s %(levelname)0.4s %(filename)s:%(lineno)d %(message)s'
    formatter = logging.Formatter(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S')

    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    file_log_handler.setLevel(logging.INFO)

    logger = logging.getLogger()
    logger.addHandler(file_log_handler)
    return logger
