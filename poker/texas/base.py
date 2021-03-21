#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:Alan
@file:base.py
@time:2021/03/13
"""

from enum import Enum
from typing import Iterable

from poker import PokerServer, PokerClient, CardSet, Player, Room


class TexasRoom(Room):

    def __init__(self):
        super(TexasRoom, self).__init__()
        self.pot = 0
        self.card_set = None
        self.status = 0

    def deal(self):
        public_cards_num = len(self.card_set.public_cards)
        if public_cards_num == 0:
            self.card_set.flop()
        elif public_cards_num == 3:
            self.card_set.turn()
        elif public_cards_num == 4:
            self.card_set.river()

    def receive_player(self, player):
        if not self.players:
            self.first_player = player
            self.last_player = player
        player.prev = self.last_player
        player.next = self.first_player
        player.enter_room(self)

    def receive_chips(self, username, chip):
        bet_player = self.players[username]
        self.pot += chip
        self.switch_player()
        if all([player.bet_success() for player in self.players.values()]):
            self.deal()
        return bet_player.next

    def switch_player(self):
        return

    def trigger(self):
        if self.is_ready():
            self.card_set = TexasCardSet(values=range(2, 15))
            self.card_set.shuffle()


class TexasCardSet(CardSet):

    def __init__(self, values):
        super(TexasCardSet, self).__init__(values)
        self.public_cards = []

    def deal(self, room):
        play_nums = len(room.players)
        for index in range(2 * play_nums):
            card = self.cards.pop(0)
            player = room.players(index % play_nums)
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

    def __init__(self, username, conn, chips=500, status=0):
        super(TexasPlayer, self).__init__(username, conn, status)
        self.chips = chips
        self.hole_cards = []
        self.call_chips = 0
        self.bet_chips = 0
        self.raise_chips = 0
        self.all_in_chips = 0
        self.checked = False
        self.folded = False
        self.bet_round_chips = 0

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

    def bet_success(self, public_bet):
        return self.bet_round_chips == public_bet or self.all_in_chips > 0


class TexasServer(PokerServer):

    def __init__(self, host='localhost', port=8889, n=5):
        super(TexasServer, self).__init__(host, port, n)
        self.players = dict()
        self.rooms = []

    def login(self, conn, username: str):
        self.players.setdefault(username, TexasPlayer(username, conn))
        conn.send("欢迎来到德州扑克！")

    def get_rooms(self):
        return self.rooms

    def open_room(self, username):
        player = self.players[username]
        room = TexasRoom()
        room.receive_player(player)
        self.rooms.append(room)


class TexasMenu(Enum):

    room_list = 'rl'
    open_room = 'or'
    enter_room = 'er'
    player_list = 'pl'
    ready = 'r'
    bet = 'bet'
    check = 'ck'
    raise_ = 'rs'
    call = 'cl'
    allin = 'ali'
    fold = 'f'
    show_cards = 'sc'
    quit = 'q'

    @classmethod
    def hill(cls):
        return cls.room_list, cls.open_room, cls.enter_room, cls.quit

    @classmethod
    def room(cls):
        return cls.ready, cls.player_list, cls.quit

    @classmethod
    def game(cls):
        return cls.bet, cls.check, cls.raise_, cls.call, cls.allin, cls.fold, cls.show_cards, cls.quit

    @classmethod
    def print(cls, menus: Iterable[Enum]):
        return '\n'.join([f"{i.name}: {i.value}" for i in menus])


class TexasClient(PokerClient):

    def __init__(self, host='localhost', port=8889):
        super(TexasClient, self).__init__(host, port)

    def login(self, player=TexasPlayer):
        super(TexasClient, self).login(player)
        self.logger.info(f"{self.player.name}，欢迎来到德州扑克")
        print(TexasMenu.print(TexasMenu.hill()))
