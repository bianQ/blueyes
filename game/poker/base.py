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
from threading import Thread


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

    @classmethod
    def encode(cls, signal, value):
        return json.dumps({'signal': signal, 'value': value}).encode()

    @classmethod
    def decode(cls, message):
        return json.loads(message.decode())


class BaseSocket:

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def get_method(self, conn: socket.socket, signal):
        func = getattr(self, signal, None)
        try:
            return func(conn)
        except AttributeError:
            conn.send(Message.encode('print', "指令错误，请重新输入"))
            raise AttributeError(f"'PokerServer' object has no method '{signal}'")
        except TypeError:
            conn.send(Message.encode('print', "指令错误，请重新输入"))
            raise TypeError(f"'PokerServer.{signal}' is not callable")
        finally:
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
            signal = conn.recv(1024)
            t = Thread(target=self.get_method, args=(conn, signal))
            t.start()


class PokerClient(BaseSocket):

    def __init__(self, host='localhost', port=8899):
        super().__init__()
        self.socket.connect((host, port))

    def run(self, callback):
        while True:
            signal = input()
            self.socket.send(signal.encode())
            data = self.socket.recv(1024)
            callback(data)


server = PokerServer()
