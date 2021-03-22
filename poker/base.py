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
import time
from typing import Iterable

from logger import create_logger
from config import PROJECT_DIR


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

    def __init__(self, values: Iterable[int]):
        self.cards = [Card(v, f) for f, v in itertools.product(range(1, 5), values)]

    def __repr__(self):
        return "<CardSet>"

    def __getitem__(self, item):
        return self.cards[item]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, room):
        pass


class Player:

    def __init__(self, name, status=0):
        self.name = name
        self.cards = []
        self.status = status
        self.room = None
        self.prev = None
        self.next = None

    def __repr__(self):
        return f"<Player[{self.name}]>"

    def enter_room(self, room):
        room.players.append(self)
        self.room = room

    def exit_room(self):
        if self.room and self in self.room.players:
            self.room.players.remove(self)
            self.room = None

    def ready(self):
        self.status = 1

    def is_ready(self):
        return self.status == 1

    def receive_card(self, card: Card):
        self.cards.append(card)

    def show_cards(self):
        return ''.join([str(card) for card in self.cards])

    def card_sort(self):
        self.cards = sorted(self.cards)


class Room:

    def __init__(self):
        self.id = int(time.time())
        self.players = []
        self.first_player = None
        self.last_player = None

    def receive_player(self, player):
        if not self.players:
            self.first_player = player
            self.last_player = player
        player.prev = self.last_player
        player.next = self.first_player
        player.enter_room(self)

    def is_ready(self):
        return all([player.is_ready() for player in self.players])


class Message:

    def __init__(self,
                 code=None,
                 signal=None,
                 args=None,
                 status=None,
                 text=None,
                 payload=None):
        self.code = code
        self.signal = signal
        self.args = args
        self.status = status
        self.text = text
        self.payload = payload

    def encode(self):
        return json.dumps(self.__dict__).encode()

    @classmethod
    def decode(cls, message):
        return Message(**json.loads(message.decode()))

    def is_success(self):
        return self.status == 200


class BaseSocket:

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.signals = {}
        self.logger = create_logger(PROJECT_DIR, 'Poker')

    def register_event(self, signal, name):
        self.signals[name] = signal


class Signal:

    def __init__(self, name):
        self.name = name
        self.deferred_functions = {}

    def add_url_rule(self, rule, view_func=None):
        self.deferred_functions[rule] = view_func

    def add(self, rule):

        def decorator(f):
            self.add_url_rule(rule, f)
            return f

        return decorator
