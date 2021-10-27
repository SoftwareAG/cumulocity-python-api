# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import pytest

from c8y_api import CumulocityApi
from c8y_api.model.identity import ExternalId

from tests import RandomNameGenerator


def test_CRUD(live_c8y: CumulocityApi, sample_device):
    """Verify that basic creation/removal and lookup of ID works as expected."""

    id_ref = RandomNameGenerator.random_name(3, '-') + '-12345'
    id_type = 'external_id_type'

    external_id = ExternalId(live_c8y, id_ref, 'external_id_type', sample_device.id)
    external_id.create()

    try:
        # retrieve the referenced object
        obj = external_id.get_object()
        # -> it is identical to the sample device
        assert obj.id == sample_device.id

        # retrieve the object ID via API
        # -> identical to sample device ID
        assert live_c8y.identity.get_id(id_ref, id_type) == sample_device.id

    finally:
        external_id.delete()

    with pytest.raises(KeyError):
        live_c8y.identity.get(id_ref, id_type)
