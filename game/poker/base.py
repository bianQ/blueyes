#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:Alan
@file:base.py
@time:2021/03/10
"""

import itertools
import random


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


class PokerServer:

    def __init__(self, host, port):
        pass


# p = Player('alan')
# print(p)
# p.receive_card(Card(14, 2))
# p.receive_card(Card(7, 1))
# print(p.show_cards())
cs = CardSet(range(2, 15))
cs.cards = sorted(cs.cards, key=lambda x: x.value)
length = 0
while length < len(cs.cards):
    print(''.join([str(i) for i in cs.cards[length: length+4]]))
    length += 4
