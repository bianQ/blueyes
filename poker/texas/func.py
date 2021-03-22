#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:Alan
@file:func.py
@time:2021/03/22
"""


def ignore_menu(player):
    ignore_list = []
    if player.menu.__name__ == 'GameMenu':
        if player != player.room.current_player or player.folded:
            ignore_list = ['bet', 'check', 'raise_', 'fold', 'call', 'allin']
        else:
            if player.room.public_bet == 0:
                ignore_list.extend(['raise_', 'call'])
            if player.room.public_bet > 0:
                ignore_list.append('check')
            if player.room.public_bet > player.chips:
                ignore_list.extend(['bet', 'raise_', 'call'])
    return ignore_list
