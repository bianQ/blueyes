#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:Alan
@file:func.py
@time:2021/03/22
"""

class CardScore:

    Pair = 0b00000001
    TowPair = 0b00000010
    Triple = 0b00000100
    Straight = 0b00001000
    Flush = 0b00010000
    FullHouse = 0b00100000
    Bomb = 0b01000000
    FlushStraight = 0b10000000

    def __init__(self, card_set):
        self.card_set = card_set
        self._score = None

    @property
    def score(self):
        if self._score:
            return self._score
        return self.level_score, self.value_score

    @property
    def level_score(self):
        score = 0
        return score

    @property
    def value_score(self):
        value = '0x'
        for card in self.card_set:
            value += hex(card.value)[-1]
        return int(value, 16)

    def is_straight(self):
        return

    def is_flush(self):
        return

    def is_triple(self):
        return

    def is_bomb(self):
        return

    def is_pair(self):
        return

    def is_flush_straight(self, score):
        return self.Straight & score != 0 and self.Flush & score != 0


def ignore_menu(player):
    ignore_list = []
    if player.menu.__name__ == 'GameMenu':
        if player != player.room.current_player or player.folded or player.room.is_pk_round():
            ignore_list = ['bet', 'check', 'raise_', 'fold', 'call', 'allin']
        else:
            if player.room.public_bet == 0:
                ignore_list.extend(['raise_', 'call'])
            if player.room.public_bet > 0:
                ignore_list.extend(['check', 'bet'])
            if player.room.public_bet > player.chips:
                ignore_list.extend(['bet', 'raise_', 'call'])
            if player.room.public_bet == player.chips:
                ignore_list.extend(['raise_'])
    return ignore_list


def max_card_sets(card_sets: list) -> list:
    card_score_dict = {}
    for card_set in card_sets:
        score = CardScore(card_set)
        card_score_dict.setdefault(score, []).append(card_set)
    max_score = max(card_score_dict)
    return card_score_dict[max_score]
