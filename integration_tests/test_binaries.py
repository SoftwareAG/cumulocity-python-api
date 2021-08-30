# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.app import CumulocityApi
from c8y_api.model import Binary


def test_upload_file():

    c8y = CumulocityApi()
    binary = Binary(filename='some_file.py', media_type='text/raw')
    reponse = c8y.binaries.upload(binary, __file__)
    assert reponse
    assert c8y.tenant_id in reponse['self']
