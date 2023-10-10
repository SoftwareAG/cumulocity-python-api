# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

# pylint: disable=redefined-outer-name

import datetime as dt
import time

import pytest
import pyotp

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


def test_get_current(live_c8y: CumulocityApi):
    """Verify that the current user can be read."""
    current1 = live_c8y.users.get(live_c8y.username)
    current2 = live_c8y.users.get_current()

    assert current1.username == current2.username
    assert current1.id == current2.id

    assert all(i in current2.effective_permission_ids for i in current1.permission_ids)


def test_current_update(live_c8y: CumulocityApi, user_c8y: CumulocityApi):
    """Verify that updating the current user works as expected."""
    current_user = user_c8y.users.get_current()

    current_user.first_name = "New"
    current_user = current_user.update()
    assert current_user.first_name == "New"

    # when the password is changed, the user_c8y needs to change
    new_password1 = '1Pass-Ruby!Workforce'
    live_c8y.users.set_password(current_user.username, new_password1)
    with pytest.raises(ValueError) as e:
        current_user.update()
    assert '401' in str(e)
    user_c8y.auth.password = new_password1
    current_user = user_c8y.users.get_current()

    # the current user password can be updated using the old password
    new_password2 = '2Pass-Ruby!Workforce'
    current_user.update_password(new_password1, new_password2)
    user_c8y.auth.password = new_password2
    current_user = user_c8y.users.get_current()
    assert dt.datetime.now(dt.timezone.utc) - current_user.last_password_change_datetime < dt.timedelta(seconds=10)


@pytest.mark.skip("This needs an TOTP enabled tenant")
def test_current_totp(live_c8y: CumulocityApi, user_c8y: CumulocityApi):
    """Verify that the TOTP settings can be updated for the current user."""
    current_user = user_c8y.users.get_current()

    # a new user without TFA won't have the TOTP activity set up
    with pytest.raises(KeyError):
        current_user.get_totp_activity()

    # the auxiliary function should intercept the KeyError
    assert not current_user.get_totp_enabled()

    # generating a secret won't enable TOTP
    secret, url = current_user.generate_totp_secret()
    assert not current_user.get_totp_activity().is_active

    # explicitly enabling the feature using different methods
    current_user.set_totp_enabled(True)
    assert current_user.get_totp_activity().is_active

    # generate and verify TOTP codes
    totp = pyotp.TOTP(secret)
    code = totp.now()
    current_user.verify_tfa(code)

    time.sleep(30)
    with pytest.raises(ValueError) as ex:
        current_user.verify_tfa(code)
    assert '403' in str(ex)

    # TODO: revoke TOTP
    # current_user.set_totp_activity(CurrentUser.TotpActivity(False))
    # assert not current_user.get_totp_activity().is_active


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


@pytest.fixture(scope='function')
def user_c8y(live_c8y: CumulocityApi, user_factory):
    new_user = user_factory()
    password = f'1Pass-{new_user.username}'
    new_user.assign_global_role('1')
    new_user.update_password(password)

    return CumulocityApi(base_url=live_c8y.base_url, tenant_id=live_c8y.tenant_id,
                         username=new_user.username, password=password)


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
