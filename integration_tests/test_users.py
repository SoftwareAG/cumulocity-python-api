# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

# pylint: disable=redefined-outer-name

import pytest

from c8y_api import CumulocityApi
from c8y_api.model import User

from tests import RandomNameGenerator


def test_CRUD(live_c8y: CumulocityApi):  # noqa (case)
    """Verify that basic CRUD functionality works."""

    username = RandomNameGenerator.random_name()
    email = f'{username}@software.ag'

    user = User(c8y=live_c8y,
                username=username, email=email,
                enabled=True)

    created_user = user.create()
    try:
        assert created_user.id == username
        assert created_user.password_strength == 'GREEN'
        assert created_user.require_password_reset
        assert created_user.tfa_enabled is False

        created_user.require_password_reset = False
        created_user.last_name = 'last_name'
        updated_user = created_user.update()

        assert updated_user.last_name == created_user.last_name
        assert updated_user.require_password_reset == created_user.require_password_reset
    finally:
        created_user.delete()

    with pytest.raises(KeyError) as e:
        live_c8y.users.get(user.username)
        assert user.username in str(e)


@pytest.fixture(scope='function')
def user_factory(live_c8y: CumulocityApi):
    """Provides a user factory function which removes the created users after
    the test execution."""

    created_users = []

    def factory_fun():
        username = RandomNameGenerator.random_name(2)
        email = f'{username}@software.ag'
        user = User(c8y=live_c8y, username=username, email=email).create()
        created_users.append(user)
        return user

    yield factory_fun

    for u in created_users:
        u.delete()


def test_set_password(live_c8y: CumulocityApi, user_factory):
    """Verify that the password of a user can be set and removed."""

    user = user_factory()

    with pytest.raises(ValueError) as ve:
        user.update_password('pw')
        assert 'least' in str(ve)

    # this is not a real password, obviously.
    # but it should meet the password requirements
    user.update_password('ja89NAk,2k23jhL_Paasd0')


def test_set_owner(live_c8y: CumulocityApi, user_factory):
    """Verify that the owner of a user can be set and removed."""

    user1 = user_factory()
    user2 = user_factory()

    # 1) set an owner using the OO method
    user1.set_owner(user2.username)
    db_user1 = live_c8y.users.get(user1.username)
    # -> owner property must be set to owner ID
    assert db_user1.owner == user2.username

    # 2) delete/unset an owner using the resource function
    live_c8y.users.set_owner(user1.username, None)
    db_user1 = live_c8y.users.get(user1.username)
    # -> owner property must be unset
    assert not db_user1.owner


def test_set_delegate(live_c8y: CumulocityApi, user_factory):
    """Verify that the delegate of a user can be set and removed."""

    user1 = user_factory()
    user2 = user_factory()

    # 1) set the delegate using the OO method
    user1.set_delegate(user2.username)
    db_user1 = live_c8y.users.get(user1.username)
    # -> owner property must be set to owner ID
    assert db_user1.delegated_by == user2.username

    # 2) delete/unset an owner using the resource function
    live_c8y.users.set_delegate(user1.username, None)
    db_user1 = live_c8y.users.get(user1.username)
    # -> owner property must be unset
    assert not db_user1.delegated_by
