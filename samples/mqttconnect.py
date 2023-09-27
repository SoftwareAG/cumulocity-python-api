# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

import logging
import threading

from dateutil import parser
from dotenv import load_dotenv
from flask import Flask, jsonify
import json

from c8y_api.app import SimpleCumulocityApp
from c8y_api.model import Measurement, Percentage, Celsius
from c8y_tk.mqttconnect import Listener


# load environment from a .env if present
load_dotenv()


# initialize cumulocity
c8yapp = SimpleCumulocityApp()
print("CumulocityApp initialized.")
print(f"URL: {c8yapp.base_url}, Tenant: {c8yapp.tenant_id}, User:{c8yapp.username}")


listener = Listener(c8yapp)
listener_thread = threading.Thread(target=listener.listen)
listener_thread.start()

def handle_temperature_measurement(topic:str, payload: bytes):
    # {"temperature":37.61135495163182,"topic":"nojava","id":"70887","count":1}
    try:
        data = json.loads(payload.decode('utf-8'))
        device_id = data['id']
        temp = float(data['temperature'])
        Measurement(c8yapp, type='c8y_Temperature', source=device_id, time='now',
                    c8y_Temperature={"Celsius": Celsius(temp)}).create()
        print(f"Measurement #{data['count']} created.")
    except Exception as ex:
        print(ex)

listener.register('python', handle_temperature_measurement)















def handle_battery_measurement(topic:str, payload: bytes):
    try:
        external_id = topic.split('/', 1)[1]
        device_id = c8yapp.identity.get_id(external_id, 'c8y_Serial')
        message = payload.decode("UTF-8").split(',')
        value = float(message[0])
        time = parser.parse(message[1] + '+00:00') if len(message) > 1  else 'now'
        m = Measurement(c8yapp, type='mqttMeasurement', source=device_id, time=time,
                        c8y_BatteryMeasurement={"Battery": Percentage(value)}).create()
        print(f"  Created measurement: #{m.id}, JSON: {m.to_full_json()}")
    except Exception as ex:
        print(ex)

# find all devices that post data via MQTT Connect
# and subscribe to corresponding topics
mqtt_devices = c8yapp.device_inventory.get_all(type='mqttConnectDevice')
for d in mqtt_devices:
    identities = c8yapp.identity.get_all(d.id)
    for i in identities:
        topic = f'nj/{i.external_id}'
        listener.register(topic, handle_battery_measurement)
        print(f"Subscribed to topic {topic} for device #{d.id}.")
















webapp = Flask(__name__)

@webapp.route("/health")
def health():
    """Return dummy health string."""
    return jsonify({'status': 'ok'})

webapp.run(host='0.0.0.0', port=80)
