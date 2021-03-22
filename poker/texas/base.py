#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:Alan
@file:base.py
@time:2021/03/13
"""
import socket
from threading import Thread
from enum import Enum

from poker import BaseSocket, CardSet, Player, Room, Message


class Element:

    def __init__(self, name, code, signal, description=None):
        self.name = name
        self.code = code
        self.signal = signal
        self.description = description

    def __str__(self):
        return f"{self.code}: {self.name}{self.description or ''}"


class HillMenu(Enum):

    __SignalMap__ = {}

    my_info = Element('个人信息', 'a', 'Texas.my_info')
    room_list = Element('房间列表', 'b', 'Texas.get_rooms')
    open_room = Element('创建房间', 'c', 'Texas.create_room')
    enter_room = Element('进入房间', 'd', 'Texas.enter_room', '（d + "空格" + 房间ID）')
    help = Element('帮助', 'h', 'Texas.help')
    quit = Element('退出游戏', 'q', 'Texas.quit')

    def __init__(self, element: Element):
        self.code = element.code
        self.signal = element.signal
        self.__class__.__SignalMap__[self.code] = self.signal

    @classmethod
    def get_signal(cls, code):
        return cls.__SignalMap__.get(code)


class RoomMenu(Enum):

    __SignalMap__ = {}

    my_info = Element('个人信息', 'a', 'Texas.my_info')
    player_list = Element('玩家列表', 'b', 'Texas.player_list')
    ready = Element('准备', 'c', 'Texas.ready')
    exit_room = Element('退出房间', 'd', 'Texas.exit_room')
    help = Element('帮助', 'h', 'Texas.help')
    quit = Element('退出游戏', 'q', 'Texas.quit')

    def __init__(self, element: Element):
        self.code = element.code
        self.signal = element.signal
        self.__class__.__SignalMap__[self.code] = self.signal

    @classmethod
    def get_signal(cls, code):
        return cls.__SignalMap__.get(code)


class GameMenu(Enum):

    __SignalMap__ = {}

    show_cards = Element('查看底牌', 'a', 'Texas.show_cards')
    bet = Element('下注', 'b', 'Texas.bet')
    check = Element('过牌', 'c', 'Texas.check')
    raise_ = Element('加注', 'd', 'Texas.raise_')
    fold = Element('弃牌', 'e', 'Texas.fold')
    call = Element('跟注', 'f', 'Texas.call')
    allin = Element('全推', 'g', 'Texas.allin')
    help = Element('帮助', 'h', 'Texas.help')
    quit = Element('退出游戏', 'q', 'Texas.quit')

    def __init__(self, element: Element):
        self.code = element.code
        self.signal = element.signal
        self.__class__.__SignalMap__[self.code] = self.signal

    @classmethod
    def get_signal(cls, code):
        return cls.__SignalMap__.get(code)


class TexasRoom(Room):

    def __init__(self):
        super(TexasRoom, self).__init__()
        self.pot = 0
        self.card_set = None
        self.status = 0
        self.public_bet = 0

    def __str__(self):
        return f"Room-{self.id}"

    def deal_public(self):
        public_cards_num = len(self.card_set.public_cards)
        if public_cards_num == 0:
            self.card_set.flop()
        elif public_cards_num == 3:
            self.card_set.turn()
        elif public_cards_num == 4:
            self.card_set.river()

    def receive_chips(self, player, chip):
        self.pot += chip
        self.public_bet = max(chip, self.public_bet)
        self.switch_player(player.next)
        if all([player.bet_success(self.public_bet) for player in self.players.values()]):
            self.deal_public()

    def switch_player(self, player):
        self.current_player = player
        if self.current_player.folded():
            self.switch_player(self.current_player.next)

    def trigger(self):
        if self.is_ready():
            self.card_set = TexasCardSet(values=range(2, 15))
            self.card_set.shuffle()

    def is_bet_success(self):
        return all([player.bet_success(self.public_bet) for player in self.players])


class TexasCardSet(CardSet):

    def __init__(self, values):
        super(TexasCardSet, self).__init__(values)
        self.public_cards = []

    def deal(self, room):
        play_nums = len(room.players)
        for index in range(2 * play_nums):
            card = self.cards.pop(0)
            player = room.players[index % play_nums]
            player.hole_cards.append(card)

    def _deal_public(self, num=1):
        self.cards.pop(0)
        for _ in range(num):
            self.public_cards.append(self.cards.pop(0))

    def flop(self):
        self._deal_public(3)

    def turn(self):
        self._deal_public()

    def river(self):
        self._deal_public()


class TexasPlayer(Player):

    def __init__(self, username, chips=500, status=0):
        super(TexasPlayer, self).__init__(username, status)
        self.chips = chips
        self.hole_cards = []
        self.call_chips = 0
        self.bet_chips = 0
        self.raise_chips = 0
        self.all_in_chips = 0
        self.checked = False
        self.folded = False
        self.bet_round_chips = 0
        self.menu = None
        self.role = None

    def __str__(self):
        return f"<{self.name}> 筹码量 {self.chips}{' 已准备' if self.is_ready() else ''}"

    def bet(self, chips):
        self.bet_chips = chips
        self.bet_round_chips += chips
        self.chips -= chips

    def raise_(self, public_bet, chips):
        self.call(public_bet)
        self.raise_chips = chips
        self.bet_round_chips += chips
        self.chips -= chips
        self.call_chips = 0

    def all_in(self):
        self.all_in_chips = self.chips
        self.bet_round_chips += self.chips
        self.chips = 0

    def check(self):
        self.checked = True

    def call(self, public_bet):
        self.call_chips = public_bet - self.bet_round_chips
        self.bet_round_chips += public_bet
        self.chips -= self.call_chips

    def fold(self):
        self.folded = True

    @property
    def is_allin(self):
        return self.all_in_chips > 0

    def bet_success(self, public_bet):
        return self.bet_round_chips == public_bet or self.all_in_chips > 0


class TexasServer(BaseSocket):

    def __init__(self, host='localhost', port=8899, n=5):
        super().__init__()
        self.host = host
        self.port = port
        self.socket.bind((host, port))
        self.socket.listen(n)
        self.rooms = []
        self.players = dict()

    def room_notice(self, room_index, text, ignore_players=None):
        ignore_players = ignore_players or []
        for conn, player in self.players.items():
            room = self.rooms[int(room_index)]
            if player not in ignore_players and player.room == room:
                conn.send(Message(text=text, status=200).encode())
        self.logger.info(text)

    def process(self, conn: socket.socket, message: Message):
        """
        根据 signal 获取执行函数并调用
        Args:
            conn: socket 连接
            message:
        """
        if message.signal:
            signal_name, signal_value = message.signal.split('.')
        else:
            player = self.players[conn]
            _signal = player.menu.get_signal(message.code)
            if _signal:
                signal_name, signal_value = _signal.split('.')
            else:
                signal_name = signal_value = None
        signal = self.signals.get(signal_name)
        if signal is None:
            self.logger.error(f"{message.signal} is not found")
            conn.send(Message(text="指令错误，请重新输入").encode())
            return
        func = signal.deferred_functions.get(signal_value)
        if func is None:
            self.logger.error(f"{message.signal} is not found")
            conn.send(Message(text="指令错误，请重新输入").encode())
            return
        func(self, conn, *message.args)

    def get_conn(self, player):
        for conn, p in self.players.items():
            if p == player:
                return conn

    def thread(self, conn):
        while True:
            try:
                rec_msg = conn.recv(1024)
                if not rec_msg:
                    return
                self.process(conn, Message.decode(rec_msg))
            except ConnectionResetError:
                self.players.pop(conn, None)

    def run(self):
        self.logger.info(f"socket:{self.host}:{self.port} 服务开启成功")
        while True:
            conn, _ = self.socket.accept()
            t = Thread(target=self.thread, args=(conn,))
            t.start()

    def open_room(self, username):
        player = self.players[username]
        room = TexasRoom()
        room.receive_player(player)
        self.rooms.append(room)


class TexasClient(BaseSocket):

    def __init__(self, host='localhost', port=8899):
        super().__init__()
        self.socket.connect((host, port))
        self.player = None
        self.status = 'running'

    def is_active(self):
        return self.status == 'running'

    def stop(self):
        self.status = 'stopped'
        self.send(signal='Texas.stop')

    def send(self, code=None, signal=None, args=()):
        self.socket.send(Message(code=code, signal=signal, args=args).encode())

    def listen_input(self):
        data = input()
        if not data:
            return
        args = [i for i in data.strip().split(' ') if i]
        if args[0] == 'q':
            self.stop()
            return
        self.send(code=args[0], args=args[1:])

    def recv(self):
        while self.is_active():
            recv = self.socket.recv(1024)
            rec_msg = Message.decode(recv)
            print(rec_msg.text)

    def run(self):
        self.login()
        t = Thread(target=self.recv)
        t.start()
        while self.is_active():
            self.listen_input()

    def login(self):
        username = input("请输入用户名：")
        if not username:
            self.login()
        self.send(signal='Texas.login', args=(username, ))
        recv = Message.decode(self.socket.recv(1024))
        self.logger.info(recv.text)
        if not recv.is_success():
            self.login()
