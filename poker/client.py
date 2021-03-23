#!/usr/bin/env python
# _*_coding:utf-8_*_

"""
@Time :     2021/3/21 17:25
@Author:    bian
@File:      client.py
"""
from threading import Thread
import socket
import json


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


class TexasClient:

    def __init__(self, host='localhost', port=8899):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.signals = {}
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
        print(recv.text)
        if not recv.is_success():
            self.login()


if __name__ == '__main__':
    client = TexasClient()
    client.run()
