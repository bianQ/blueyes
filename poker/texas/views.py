#!/usr/bin/env python
# _*_coding:utf-8_*_

"""
@Time :     2021/3/21 17:41
@Author:    bian
@File:      views.py
"""
import socket
from functools import wraps

from poker import Message
from poker.texas import texas_sg
from poker.texas import TexasServer, TexasPlayer, HillMenu, TexasRoom, RoomMenu


def _format_menu(menu):
    return '\n'.join([str(m.value) for m in menu])


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
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
    text = '\n'.join([f"{i}\t{r}" for i, r in enumerate(server.rooms)]) or '无房间'
    conn.send(Message(text=text, status=200).encode())


@texas_sg.add('create_room')
@login_required
def create_rooms(server: TexasServer, conn):
    room = TexasRoom()
    player = server.players[conn]
    room.receive_player(player)
    server.rooms.append(room)
    player.menu = RoomMenu
    text = f"创建房间成功，房间ID {room.id}\n" \
           f"输入 h/H 查看帮助菜单"
    conn.send(Message(text=text, status=200).encode())


@texas_sg.add('enter_room')
@login_required
def enter_room(server: TexasServer, conn, room_index):
    player = server.players[conn]
    room = server.rooms[int(room_index)]
    room.receive_player(player)
    player.menu = RoomMenu
    text = f"进入房间成功，房间ID {room.id}\n" \
           f"输入 h/H 查看帮助菜单"
    conn.send(Message(text=text, status=200).encode())
    server.room_notice(room_index, text=f"玩家<{player.name}> 进入房间", ignore_players=[player])


@texas_sg.add('exit_room')
@login_required
def exit_room(server: TexasServer, conn):
    player = server.players[conn]
    room_index = server.rooms.index(player.room)
    player.exit_room()
    player.menu = HillMenu
    text = f"已退出房间\n" \
           f"输入 h/H 查看帮助菜单"
    conn.send(Message(text=text, status=200).encode())
    server.room_notice(room_index, text=f"玩家<{player.name}> 退出房间", ignore_players=[player])


@texas_sg.add('my_info')
@login_required
def my_info(server: TexasServer, conn):
    player = server.players[conn]
    text = f"玩家<{player.name}>，筹码量 {player.chips}"
    conn.send(Message(text=text, status=200).encode())


@texas_sg.add('player_list')
@login_required
def player_list(server: TexasServer, conn):
    player = server.players[conn]
    room = player.room
    text = '\n'.join([str(p) for p in room.players])
    conn.send(Message(text=text, status=200).encode())


@texas_sg.add('ready')
@login_required
def ready(server: TexasServer, conn):
    player = server.players[conn]
    player.ready()
    conn.send(Message(text=f"已准备，等待其他玩家准备", status=200).encode())
    room = player.room
    if room.is_ready():
        room_index = server.rooms.index(room)
        server.room_notice(room_index, text="牌局开始")
        room.trigger()
        room.card_set.deal(room)
        server.room_notice(room_index, text="发牌完成")


@texas_sg.add('help')
@login_required
def help_list(server: TexasServer, conn):
    player = server.players[conn]
    conn.send(Message(text=_format_menu(player.menu), status=200).encode())


@texas_sg.add('stop')
@login_required
def stop(server: TexasServer, conn):
    server.players.pop(conn, None)
    conn.send(Message(text='', status=200).encode())
