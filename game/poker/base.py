#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:Alan
@file:base.py
@time:2021/03/10
"""
import json
import itertools
import random
import socket
import logging
from logging import NullHandler
from threading import Thread


log = logging.getLogger(__name__)


class Card:

    value_dict = {
        11: 'J',
        12: 'Q',
        13: 'K',
        14: 'A'
    }
    flip_dict = {
        1: '♠',
        2: '♥',
        3: '♣',
        4: '♦'
    }

    def __init__(self, value: int, flip: int):
        self.value = value
        self.flip = self.flip_dict[flip]

    def __gt__(self, other):
        return self.value > other.value

    def __repr__(self):
        return f"<Card[{self.flip}{self.value_dict.get(self.value, self.value)}]>"

    def __str__(self):
        return f"[{self.flip}{self.value_dict.get(self.value, self.value)}]"

    def is_ace(self):
        return self.value == 14


class CardSet:

    def __init__(self, values):
        self.cards = [Card(v, f) for f, v in itertools.product(range(1, 5), values)]

    def __repr__(self):
        return "<CardSet>"

    def __getitem__(self, item):
        return self.cards[item]

    def shuffle(self):
        random.shuffle(self.cards)

    def distribute(self, num=1):
        pass


class Player:

    def __init__(self, name):
        self.name = name
        self.cards = []

    def __repr__(self):
        return f"<Player[{self.name}]>"

    def receive_card(self, card: Card):
        self.cards.append(card)

    def show_cards(self):
        return ''.join([str(card) for card in self.cards])

    def card_sort(self):
        self.cards = sorted(self.cards)


class Message:

    def __init__(self, signal, value):
        self.signal = signal
        self.value = value

    def encode(self):
        return json.dumps({'signal': self.signal, 'value': self.value}).encode()

    @classmethod
    def decode(cls, message):
        return Message(**json.loads(message.decode()))


class BaseSocket:

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def process(self, conn: socket.socket, message: Message, logger=log, is_server=True):
        """
        根据 signal 获取执行函数并调用
        Args:
            conn: socket 连接
            message:
            logger: 日志处理模块
            is_server: 是否是服务端
        """
        func = getattr(self, message.signal, None)
        send_msg = Message(signal='print', value="指令错误，请重新输入")
        try:
            send_msg = func(conn, message.value)
        except AttributeError:
            logger.error(f"'PokerServer' object has no method '{send_msg.signal}'")
        except TypeError:
            logger.error(f"'PokerServer.{send_msg.signal}' is not callable")
        finally:
            if is_server:
                conn.send(send_msg.encode())
                conn.close()


class PokerServer(BaseSocket):

    def __init__(self, host='localhost', port=8899, n=5):
        super().__init__()
        self.socket.bind((host, port))
        self.socket.listen(n)
        self.rooms = []

    def run(self):
        while True:
            conn, _ = self.socket.accept()
            rec_msg = conn.recv(1024)
            t = Thread(target=self.process, args=(conn, rec_msg))
            t.start()


class PokerClient(BaseSocket):

    def __init__(self, host='localhost', port=8899):
        super().__init__()
        self.socket.connect((host, port))

    def print(self, ):
        pass

    def run(self):
        while True:
            data = input()
            signal, value = data.strip().split(' ')
            send_msg = Message(signal=signal, value=value.strip())
            self.process(self.socket, send_msg)
            rec_msg = self.socket.recv(1024)
            self.print(rec_msg)


server = PokerServer()
