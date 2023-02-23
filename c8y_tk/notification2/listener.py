# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import asyncio
from typing import Callable
import websockets as ws
import json as js

from _main_api import CumulocityApi


class Listener(object):

    def __init__(self, c8y: CumulocityApi, subscription_name: str, on_message: Callable[["Message"], None]):
        self.c8y = c8y
        self.subscription_name = subscription_name
        self.on_message = on_message

        self._event_loop = asyncio.new_event_loop()
        self._outbound_queue = []
        self._current_uri = None
        self._is_closed = False
        self._connection = None

    def listen(self):
        self._event_loop.run_until_complete(self._listen())
        print("done running")

    def receive(self, timeout=None) -> "Message":
        return self._event_loop.run_until_complete(self._receive(timeout))

    def close(self, asynchronous=False):
        future = asyncio.run_coroutine_threadsafe(self._close(), self._event_loop)
        if not asynchronous:
            future.result()

    def send(self, payload: str, asynchronous=False) -> None:
        future = asyncio.run_coroutine_threadsafe(self._send(payload), self._event_loop)
        if not asynchronous:
            future.result()

    def ack(self, message: str, asynchronous=False) -> None:
        future = asyncio.run_coroutine_threadsafe(self._ack(message), self._event_loop)
        if not asynchronous:
            future.result()

    async def _get_connection(self) -> ws.WebSocketClientProtocol:
        if not self._connection:
            if not self._current_uri:
                token = self.c8y.notification2_tokens.generate(self.subscription_name, expires=2)
                self._current_uri = self.c8y.notification2_tokens.build_websocket_uri(token)
            try:
                self._connection = await ws.connect(self._current_uri)
                print(f"Connection established: {self._connection}")
            except ws.ConnectionClosed as e:
                print(f"Connection closed: {e}")
                self._connection = None
                self._current_uri = None  # maybe the URI can be reused if not expired?

        return self._connection

    async def _receive(self, timeout: float=None):
        print("here we are")
        websocket = await self._get_connection()
        print("got connection")
        payload = await asyncio.wait_for(websocket.recv(), timeout)
        print("got payload")
        return Message(listener=self, payload=payload)

    async def _close(self):
        self._is_closed = True
        c = await self._get_connection()
        await c.close()

    async def _ack(self, message: str) -> asyncio.Task:
        msg_id = message.splitlines()[0]
        return await self._send(msg_id)

    async def _send(self, msg: str) -> asyncio.Task:
        websocket = await self._get_connection()
        task = asyncio.ensure_future(websocket.send(msg))
        return task

    async def _listen(self):
        while not self._is_closed:
            try:
                c = await self._get_connection()
                message = await c.recv()
                print(f"Received message: {message}")
                self.on_message(Message(listener=self, payload=message))
            except ws.ConnectionClosed as e:
                print(f"Websocket connection closed: {e}")


class Message(object):

    def __init__(self, listener: Listener, payload: str):
        self.listener = listener
        self.raw = payload
        parts = payload.splitlines(keepends=False)
        assert len(parts) > 3
        self.message_id = parts[0]
        self.source = parts[1]
        self.action = parts[2]
        self.body = parts[len(parts)-1]

    @property
    def json(self):
        return js.loads(self.body)

    def ack(self):
        self.listener.send(self.message_id)
