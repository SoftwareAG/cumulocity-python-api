# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import pytest

from c8y_api import CumulocityApi
from c8y_api.model import Operation

from tests import RandomNameGenerator


def test_CRUD(live_c8y: CumulocityApi, sample_device):
    """Verify that basic creation, lookup and update of Operations works as expected."""

    # create operation
    #testOperation = Operation(c8y_api, sample_device.id, "Test operation")
    testOperation = Operation(live_c8y, sample_device.id, 'Shell command', c8y_Command={'text': 'myCommand'})
    testOperation.create()

    try:
        # query pending operations
        operationList = live_c8y.operations.get_all(agentId=sample_device.id, status='PENDING', page_size=1)
        pending_operation = operationList[0]
        # -> it is identical to the sample device
        assert pending_operation.status == 'PENDING'
        assert pending_operation.deviceId == sample_device.id

    finally:
        pending_operation.status = 'EXECUTING'
        pending_operation.update()
