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
from poker.texas import TexasServer, TexasPlayer, HillMenu, TexasRoom, RoomMenu, GameMenu
from poker.texas.func import ignore_menu


def _format_menu(menu, ignore_list=None):
    ignore_list = ignore_list or []
    return '\n'.join([str(m.value) for m in menu if m.name not in ignore_list])


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
        for p in room.players:
            p.menu = GameMenu
            cards = ''.join([str(card) for card in p.hole_cards])
            server.logger.info(f"玩家<{p.name}>，底牌{cards}")
            player_conn = server.get_conn(p)
            player_conn.send(Message(text=p.show_cards(), status=200).encode())
            if p == room.current_player:
                player_conn.send(Message(text="请下注", status=200).encode())
        server.room_notice(
            room_index, text=f"等待玩家<{room.current_player.name}>下注", ignore_players=[room.current_player])


@texas_sg.add('bet')
@login_required
def bet(server: TexasServer, conn, chips):
    player = server.players[conn]
    room_index = server.rooms.index(player.room)
    player.bet(int(chips))
    conn.send(Message(text=f"下注{chips}成功").encode())
    server.room_notice(
        room_index,
        text=f"玩家<{player.name}>下注{chips}，当前注码{player.bet_round_chips}，"
             f"底池{player.room.pot + player.bet_round_chips}",
        ignore_players=[player])
    player.room.receive_chips(player, int(chips))
    if not player.room.is_bet_success() and player.room.is_ready():
        current_player_conn = server.get_conn(player.room.current_player)
        server.room_notice(
            room_index,
            text=f"等待玩家<{player.room.current_player.name}>下注",
            ignore_players=[player.room.current_player])
        current_player_conn.send(Message(text="请下注", status=200).encode())


@texas_sg.add('check')
@login_required
def check(server: TexasServer, conn):
    player = server.players[conn]
    room_index = server.rooms.index(player.room)
    player.check()
    conn.send(Message(text=f"check成功").encode())
    server.room_notice(
        room_index,
        text=f"玩家<{player.name}>check",
        ignore_players=[player]
    )
    player.room.receive_chips(player, 0)
    if not player.room.is_bet_success() and player.room.is_ready():
        current_player_conn = server.get_conn(player.room.current_player)
        server.room_notice(
            room_index,
            text=f"等待玩家<{player.room.current_player.name}>下注",
            ignore_players=[player.room.current_player])
        current_player_conn.send(Message(text="请下注", status=200).encode())


@texas_sg.add('call')
@login_required
def call(server: TexasServer, conn):
    player = server.players[conn]
    room_index = server.rooms.index(player.room)
    public_bet = player.room.public_bet
    player.call(public_bet)
    print(public_bet, player.bet_round_chips)
    conn.send(Message(text=f"跟注{player.call_chips}").encode())
    server.room_notice(
        room_index,
        text=f"玩家<{player.name}>跟注{player.call_chips}，当前注码{player.bet_round_chips}，"
             f"底池{player.room.pot + player.call_chips}",
        ignore_players=[player]
    )
    player.room.receive_chips(player, player.call_chips)
    if not player.room.is_bet_success() and player.room.is_ready():
        current_player_conn = server.get_conn(player.room.current_player)
        server.room_notice(
            room_index,
            text=f"等待玩家<{player.room.current_player.name}>下注",
            ignore_players=[player.room.current_player])
        current_player_conn.send(Message(text="请下注", status=200).encode())


@texas_sg.add('raise_')
@login_required
def raise_(server: TexasServer, conn, chips):
    player = server.players[conn]
    room_index = server.rooms.index(player.room)
    public_bet = player.room.public_bet
    bet_chips = player.bet_round_chips
    player.raise_(public_bet, int(chips))
    new_bet_chips = player.bet_round_chips - bet_chips
    conn.send(Message(text=f"加注到{public_bet + int(chips)}").encode())
    server.room_notice(
        room_index,
        text=f"玩家<{player.name}>加注，当前注码{player.bet_round_chips}，"
             f"底池{player.room.pot + new_bet_chips}",
        ignore_players=[player])
    player.room.receive_chips(player, new_bet_chips)
    # 加注需要校准注码
    player.room.public_bet = player.bet_round_chips
    if not player.room.is_bet_success() and player.room.is_ready():
        current_player_conn = server.get_conn(player.room.current_player)
        server.room_notice(
            room_index,
            text=f"等待玩家<{player.room.current_player.name}>下注",
            ignore_players=[player.room.current_player])
        current_player_conn.send(Message(text="请下注", status=200).encode())


@texas_sg.add('fold')
@login_required
def fold(server: TexasServer, conn):
    player = server.players[conn]
    room_index = server.rooms.index(player.room)
    player.fold()
    conn.send(Message(text=f"已弃牌").encode())
    server.room_notice(room_index, text=f"玩家<{player.name}>弃牌", ignore_players=[player])
    player.room.receive_chips(player, 0)
    if not player.room.is_bet_success() and player.room.is_ready():
        current_player_conn = server.get_conn(player.room.current_player)
        server.room_notice(
            room_index,
            text=f"等待玩家<{player.room.current_player.name}>下注",
            ignore_players=[player.room.current_player])
        current_player_conn.send(Message(text="请下注", status=200).encode())


@texas_sg.add('allin')
@login_required
def allin(server: TexasServer, conn):
    player = server.players[conn]
    room_index = server.rooms.index(player.room)
    player.allin()
    conn.send(Message(text=f"All in {player.allin_chips}").encode())
    server.room_notice(
        room_index,
        text=f"玩家<{player.name}> 全推，当前注码{max(player.room.public_bet, player.bet_round_chips)}，"
             f"底池{player.room.pot + player.allin_chips}",
        ignore_players=[player])
    player.room.receive_chips(player, player.allin_chips)
    if not player.room.is_bet_success() and player.room.is_ready():
        current_player_conn = server.get_conn(player.room.current_player)
        server.room_notice(
            room_index,
            text=f"等待玩家<{player.room.current_player.name}>下注",
            ignore_players=[player.room.current_player])
        current_player_conn.send(Message(text="请下注", status=200).encode())


@texas_sg.add('show_cards')
@login_required
def show_cards(server: TexasServer, conn):
    player = server.players[conn]
    conn.send(Message(text=player.show_cards()).encode())


@texas_sg.add('help')
@login_required
def help_list(server: TexasServer, conn):
    player = server.players[conn]
    ignore_list = ignore_menu(player)
    conn.send(Message(text=_format_menu(player.menu, ignore_list), status=200).encode())


@texas_sg.add('stop')
@login_required
def stop(server: TexasServer, conn):
    server.players.pop(conn, None)
    conn.send(Message(text='', status=200).encode())
