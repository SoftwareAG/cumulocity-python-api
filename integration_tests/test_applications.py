# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api import CumulocityApi

import pytest


def test_select_name(live_c8y: CumulocityApi):
    """Verify that select by name works."""
    apps = live_c8y.applications.get_all(name='devicemanagement')
    assert len(apps) == 1
    app = apps[0]

    assert app.name == 'devicemanagement'
    assert app.owner == 'management'
    assert app.type == 'HOSTED'
    assert app.availability == 'MARKET'


@pytest.mark.parametrize('param, param_func', [
    ('type', lambda x: 'HOSTED'),
    ('user', lambda x: x.username),
    ('owner', lambda x: 'management'),
    ('tenant', lambda x: x.tenant_id),
    ('subscriber', lambda x: x.tenant_id),
    ('provided_for', lambda x: x.tenant_id),
])
def test_selects(live_c8y: CumulocityApi, param, param_func):
    """Verify that select/get_all works with all available filters."""
    kwargs = {param: param_func(live_c8y)}
    apps = live_c8y.applications.get_all(**kwargs)
    assert apps
