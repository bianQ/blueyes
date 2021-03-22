#!/usr/bin/env python
# _*_coding:utf-8_*_

"""
@Time :     2021/3/21 17:41
@Author:    bian
@File:      views.py
"""
import socket

from poker import Message
from poker.texas import texas_sg
from poker.texas import TexasServer, TexasPlayer, HillMenu


def _format_menu(menu):
    return '\n'.join([str(m.value) for m in menu])


def login_required(*args, **kwargs):
    def wrapper(func):
        conn = args[1]
        if not isinstance(conn, socket.socket):
            return
        if conn not in args[0].players:
            conn.send("请先登录".encode())
            return
        return func(*args, **kwargs)
    return wrapper


@texas_sg.add('login')
def login(server: TexasServer, conn, username, chips=None):
    if username in [player.name for player in server.players.values()]:
        conn.send(Message(text=f"{username}已登录", status=400).encode())
        return
    player = TexasPlayer(username)
    player.menu = HillMenu
    server.players[conn] = player
    server.logger.info(f"玩家<{username}>登录游戏")
    conn.send(Message(text=f"{username}，欢迎来到德州扑克", status=200).encode())
    conn.send(Message(text='输入 h/H 查看帮助菜单').encode())


@texas_sg.add('get_rooms')
@login_required
def get_rooms(server: TexasServer, conn):
    for i in server.rooms:
        print(i)
    pass


@texas_sg.add('my_info')
@login_required
def get_rooms(server: TexasServer, conn):
    pass
