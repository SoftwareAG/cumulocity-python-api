# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

from typing import Callable
from urllib.parse import urlparse

import paho.mqtt.client as mqtt

from c8y_api import CumulocityApi


class Listener:

    def __init__(self, c8y: CumulocityApi):
        self.c8y = c8y
        self.mqtt_client = mqtt.Client(f'mqttconnect_{c8y.username}')
        self.subscribers = {}

    def register(self, topic: str, callback: Callable[[str, bytes], None]):
        self.subscribers[topic] = callback
        self.mqtt_client.subscribe(topic)

    def deregister(self, topic: str):
        del(self.subscribers[topic])

    def listen(self):

        def on_message(mqttc, obj, msg):
            print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
            self.subscribers[msg.topic](msg.topic, msg.payload)

        def on_connect(mqttc, obj, flags, rc):
            print("rc: " + str(rc))

        def on_publish(mqttc, obj, mid):
            print("mid: " + str(mid))

        def on_subscribe(mqttc, obj, mid, granted_qos):
            print("Subscribed: " + str(mid) + " " + str(granted_qos))

        def on_log(mqttc, obj, level, string):
            print(string)

        self.mqtt_client.on_message = on_message
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_publish = on_publish
        self.mqtt_client.on_subscribe = on_subscribe
        self.mqtt_client.on_log = on_log
        self.mqtt_client.username_pw_set(self.c8y.auth.username, self.c8y.auth.password)
        self.mqtt_client.connect(urlparse(self.c8y.base_url).netloc, 2883, 60)
        for topic in self.subscribers:
            self.mqtt_client.subscribe(topic)
        self.mqtt_client.loop_forever()

    def close(self):
        self.mqtt_client.disconnect()
