#!/usr/bin/env python
# _*_coding:utf-8_*_

"""
@Time :     2021/3/21 17:23
@Author:    bian
@File:      server.py
"""

from poker.texas.base import TexasServer
from poker.texas import texas_sg


server = TexasServer()
server.register_event(texas_sg, 'Texas')
server.run()
