# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.model import Measurement


def test_measurement_parsing():
    """Verify that parsing of a Measurement works as expected."""

    measurement_json = {
        'id': '12345',
        'self': 'https://...',
        'type': 'c8y_Measurement',
        'source': {'id': '54321', 'self': 'https://...'},
        'time': '2020-31-12T22:33:44,567Z',
        'c8y_Measurement': {'c8y_temperature': {'unit': 'x', 'value': 12.3}}
    }
    m = Measurement.from_json(measurement_json)

    assert m.id == '12345'
    assert m.source == '54321'
    assert m.type == 'c8y_Measurement'
    assert m.time == '2020-31-12T22:33:44,567Z'
    assert m.c8y_Measurement.c8y_temperature.value == 12.3

    expected_full_json = {
        'type': m.type,
        'source': {'id': m.source},
        'time': m.time,
        'c8y_Measurement': {'c8y_temperature': {'unit': 'x', 'value': 12.3}}
    }
    assert m.to_full_json() == expected_full_json
