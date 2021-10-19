# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import json
import os

from c8y_api.model import Application


def test_parsing():
    """Verify that parsing a Application from JSON works."""
    path = os.path.dirname(__file__) + '/application.json'
    with open(path, encoding='utf-8', mode='rt') as f:
        application_json = json.load(f)
    application = Application.from_json(application_json)

    assert application.id == application_json['id']
    assert application.type == application_json['type']
    assert application.availability == application_json['availability']
    assert application.owner == application_json['owner']['tenant']['id']
