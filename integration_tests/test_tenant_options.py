# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import pytest

from c8y_api.app import CumulocityApi
from c8y_api.model.tenant_options import TenantOption

from tests import RandomNameGenerator


def test_get_all_mapped(live_c8y: CumulocityApi):
    """Verify that select by name works."""
    options = live_c8y.tenant_options.get_all_mapped(category='two-factor-authentication')
    assert options
    assert 'enforced' in options


def test_crud(live_c8y: CumulocityApi):
    """Verify that create/read/update/delete works for tenant options using
    the object-oriented functions."""

    category = RandomNameGenerator.random_name(2)

    option = None
    try:

        # 1) creating an option
        option = TenantOption(category=category, key='my_key', value='test value')
        option.c8y = live_c8y
        option = option.create()
        # check whether option was created and value matches
        assert live_c8y.tenant_options.get(option.category, option.key).value == 'test value'

        # 2) update the option
        option.value = 'new value'
        option = option.update()
        # check whether option was updated in object and database
        assert option.value == 'new value'
        assert live_c8y.tenant_options.get_value(option.category, option.key) == 'new value'

        # 3) delete the option
        option.delete()
        with pytest.raises(KeyError):
            live_c8y.tenant_options.get(option.category, option.key)
        option = None

    # pylint: disable=broad-except
    except Exception as e:
        assert False, "Unexpected exception: " + str(e)

    finally:
        if option:
            option.delete()


def test_crud_2(live_c8y: CumulocityApi):
    """Verify that create/read/update/delete works for tenant options using
    the procedural functions."""

    category = RandomNameGenerator.random_name(2)

    option = None
    try:

        # 1) creating an option
        option = TenantOption(category=category, key='my_key', value='test value')
        live_c8y.tenant_options.create(option)
        # check whether option was created and value matches
        assert live_c8y.tenant_options.get_value(option.category, option.key) == 'test value'

        # 2) update the option
        option.value = 'new value'
        live_c8y.tenant_options.update(option)
        # check whether option was updated in object and database
        assert live_c8y.tenant_options.get_value(option.category, option.key) == 'new value'

        # 3) delete the option
        live_c8y.tenant_options.delete(option)
        with pytest.raises(KeyError):
            live_c8y.tenant_options.get(option.category, option.key)
        option = None

    # pylint: disable=broad-except
    except Exception as e:
        assert False, "Unexpected exception: " + str(e)

    finally:
        if option:
            live_c8y.tenant_options.delete(option)


def test_set_value_and_update_and_delete_by(live_c8y: CumulocityApi):
    """Verify that functions set_value, update_by and delete_by work
    as expected."""

    category = RandomNameGenerator.random_name(2)
    key = 'my_key'

    try:

        # 1) creating an option
        live_c8y.tenant_options.set_value(category=category, key='my_key', value='test value')

        # 2) update the option
        live_c8y.tenant_options.update_by(category, {key: 'new value'})
        # check whether option was updated in object and database
        assert live_c8y.tenant_options.get_value(category, key) == 'new value'

        # 3) delete the option
        live_c8y.tenant_options.delete_by(category, key)
        with pytest.raises(KeyError):
            live_c8y.tenant_options.get(category, key)

    # pylint: disable=broad-except
    except Exception as e:
        assert False, "Unexpected exception: " + str(e)

    finally:
        try:
            live_c8y.tenant_options.delete_by(category, key)
        except KeyError:
            pass
