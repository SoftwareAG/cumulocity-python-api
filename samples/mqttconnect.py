# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations


from dotenv import load_dotenv
from inputimeout import inputimeout, TimeoutOccurred
import paho.mqtt.client as mqtt

from c8y_api import CumulocityApi

from c8y_api.app import SimpleCumulocityApp
from c8y_api.model import Celsius, Device, Measurement, Operation

# A simple (per tenant) Cumulocity application can be created just like this.
# The authentication information is read from the standard Cumulocity
# environment variables that are injected into the Docker container.

load_dotenv()  # load environment from a .env if present
c8y = SimpleCumulocityApp()
print("CumulocityApp initialized.")
print(f"{c8y.base_url}, Tenant: {c8y.tenant_id}, User:{c8y.username}")

class MqttConnectListener():

    def __init__(self, c8y: CumulocityApi):
        self.c8y = c8y
        self.mqtt_client = mqtt.Client(f'mqttconnect_{c8y.username}')
        self.subscribers = {}

    def add(self, topic: str, callback):
        self.subscribers[topic] = callback
        self.mqtt_client.subscribe(topic)



    def listen(self):
        def on_message(mqttc, obj, msg):
            print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
            self.subscribers[msg.topic](msg.payload)

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
        self.mqtt_client.connect("hackathon1.dev.c8y.io", 2883, 60)
        for topic in self.subscribers:
            self.mqtt_client.subscribe(topic)

        self.mqtt_client.loop_forever()

# The SimpleCumulocityApp behaves just like any other CumulocityApi instance,
# e.g. ...
def handle_battery_measurement(msg: str):
    print('battery measurement successfully handled.')


listener = MqttConnectListener(c8y)
listener.add('bat', handle_battery_measurement)
listener.listen()
#
#
# c8y.mqttconnect.subscribe('bat', handle_battery_measurement)
# c8y.mqttconnect.subscribe('bat', handle_battery_measurement)
# c8y.mqttconnect.subscribe('bat', handle_battery_measurement)
# c8y.mqttconnect.subscribe('bat', handle_battery_measurement)
# c8y.mqttconnect.subscribe('bat', handle_battery_measurement)
# c8y.mqttconnect.loop(
#



#
#
#
# def on_connect(mqttc, obj, flags, rc):
#     print("rc: " + str(rc))
#
#
# def on_message(mqttc, obj, msg):
#     print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
#
#
# def on_publish(mqttc, obj, mid):
#     print("mid: " + str(mid))
#
#
# def on_subscribe(mqttc, obj, mid, granted_qos):
#     print("Subscribed: " + str(mid) + " " + str(granted_qos))
#
#
# def on_log(mqttc, obj, level, string):
#     print(string)
#
#
# # If you want to use a specific client id, use
# # mqttc = mqtt.Client("client-id")
# # but note that the client id must be unique on the broker. Leaving the client
# # id parameter empty will generate a random id for you.
# mqttc = mqtt.Client('nj_pythonapi')
# mqttc.on_message = on_message
# mqttc.on_connect = on_connect
# mqttc.on_publish = on_publish
# mqttc.on_subscribe = on_subscribe
# # Uncomment to enable debug messages
# mqttc.on_log = on_log
# mqttc.username_pw_set('t287/admin', 'Dq8urP7PgfB@Wf4w.9Xf')
# # mqttc.tls_set()
# mqttc.connect("hackathon1.dev.c8y.io", 2883, 60)
# mqttc.subscribe("nj", 0)
# mqttc.subscribe("bat", 0)
#
# mqttc.loop_forever()