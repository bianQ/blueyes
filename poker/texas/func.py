#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:Alan
@file:func.py
@time:2021/03/22
"""
from typing import Iterable
from collections import Counter


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
        self._card_value_count = Counter([card.value for card in self.card_set])
        self._max_value_count = max(self._card_value_count.values())

    def __gt__(self, other):
        return self.score > other.score

    @property
    def score(self):
        if self._score:
            return self._score
        return self.level_score, self.value_score

    @property
    def level_score(self):
        score = 0
        if self.is_straight():
            score |= self.Straight
        if self.is_flush():
            score |= self.Flush
        if self.is_flush_straight(score):
            score |= self.FlushStraight
        if self.is_bomb():
            score |= self.Bomb
        if self.is_full_house():
            score |= self.FullHouse
        if self.is_triple():
            score |= self.Triple
        if self.is_two_pair():
            score |= self.TowPair
        if self.is_pair():
            score |= self.Pair
        return score

    @property
    def value_score(self):
        value = '0x'
        for card in self.card_set[::-1]:
            value += hex(card.value)[-1]
        return int(value, 16)

    def is_straight(self):
        four_card_straight = all([right.value - left.value == 1 for
                                  left, right in zip(self.card_set[:4], self.card_set[1:])])
        if four_card_straight:
            if self.card_set[-1].value - self.card_set[-2].value == 1:
                return True
            if self.card_set[0].value == 2 and self.card_set[-1].is_ace():
                return True
        return False

    def is_flush(self):
        return len(set(card.flip for card in self.card_set)) == 1

    def is_triple(self):
        return self._max_value_count == 3

    def is_bomb(self):
        return self._max_value_count == 4

    def is_pair(self):
        return self._max_value_count == 2

    def is_full_house(self):
        return self._max_value_count == 3 and len(self._card_value_count) == 2

    def is_two_pair(self):
        return self._max_value_count == 2 and len(self._card_value_count) == 3

    def is_flush_straight(self, score):
        return self.Straight & score != 0 and self.Flush & score != 0


def ignore_menu(player):
    ignore_list = []
    if player.menu.__name__ == 'GameMenu':
        if player.room.is_ready() and \
                (player != player.room.current_player or player.folded or
                 (player.room.is_bet_success() and player.room.is_pk_round())):
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


def max_card_sets(card_sets: Iterable) -> list:
    card_score_dict = {}
    for card_set in card_sets:
        score = CardScore(card_set)
        card_score_dict.setdefault(score, []).append(card_set)
    max_score = max(card_score_dict)
    return card_score_dict[max_score]
