# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

import pytest

from c8y_api.model import GlobalRole
from tests import RandomNameGenerator


def test_CRUD(live_c8y: CumulocityApi):  # noqa (case)
    """Verify that basic CRUD functionality works."""

    rolename = RandomNameGenerator.random_name()

    role = GlobalRole(c8y=live_c8y, name=rolename, description=f'{rolename} description')

    created_role = role.create()
    try:
        # 1) assert correct creation
        assert created_role.id
        assert created_role.name == rolename
        assert rolename in created_role.description

        # 2) update updatable fields
        created_role.name = f'{rolename}_2'
        created_role.description = f'Updated {created_role.description}'
        updated_role = created_role.update()

        # 3) assert updates
        assert updated_role.name == created_role.name
        assert updated_role.description == created_role.description
    finally:
        created_role.delete()

    # 4) assert deletion
    with pytest.raises(KeyError) as e:
        live_c8y.global_roles.get(rolename)
        assert rolename in str(e)
