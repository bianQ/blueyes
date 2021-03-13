#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:Alan
@file:server.py
@time:2021/03/13
"""

from game.poker.base import PokerServer, CardSet, Player, Room, Message


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

    def __init__(self, host='localhost', port=8899, n=5):
        super(TexasServer, self).__init__(host, port, n)
        self.players = dict()
        self.rooms = []

    def login(self, conn, username: str):
        self.players.setdefault(username, TexasPlayer(username, conn))
        conn.send("欢迎来到德州扑克！")

    def get_rooms(self):
        return self.rooms

    def create_room(self, username):
        player = self.players[username]
        room = TexasRoom()
        room.receive_player(player)
        self.rooms.append(room)
