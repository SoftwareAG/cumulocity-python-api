# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

# pylint: disable=redefined-outer-name

import json
import os

import pytest

from c8y_api.model import User


@pytest.fixture(scope='function')
def sample_user() -> User:
    """Provide a sample user, read from JSON file."""
    path = os.path.dirname(__file__) + '/user.json'
    with open(path, encoding='utf-8', mode='rt') as f:
        user_json = json.load(f)

    return User.from_json(user_json)


def test_parsing():
    """Verify that parsing a User from JSON works."""

    # 1) read a sample user from file
    path = os.path.dirname(__file__) + '/user.json'
    with open(path, encoding='utf-8', mode='rt') as f:
        user_json = json.load(f)

    user = User.from_json(user_json)

    # 2) verify that all parsed fields match the file counterpart
    assert user.id == user_json['id']
    assert user.username == user_json['userName']
    assert user.email == user_json['email']
    assert user.enabled == user_json['enabled']
    assert user.display_name == user_json['displayName']
    assert user.first_name == user_json['firstName']
    assert user.last_name == user_json['lastName']
    # assert user.owner == user_json['owner']
    # assert user.delegated_by == user_json['delegatedBy']
    assert user.password_strength == user_json['passwordStrength']
    assert user.tfa_enabled == user_json['twoFactorAuthenticationEnabled']
    assert user.require_password_reset == user_json['shouldResetPassword']

    # 3) referenced sets are parsed as well
    global_role_ids = {str(r['group']['id']) for r in user_json['groups']['references']}
    permission_ids = {r['role']['id'] for r in user_json['roles']['references']}
    assert user.global_role_ids == global_role_ids
    assert user.permission_ids == permission_ids


def test_formatting(sample_user: User):
    """Verify that user formatting works."""
    user_json = sample_user.to_json()
    assert 'id' not in user_json


def test_updating(sample_user: User):
    """Verify that updating the user properties are recorded properly."""
    # pylint: disable=protected-access

    # 1) some fields are readonly
    sample_user.id = 'x'
    sample_user.username = 'x'
    sample_user.owner = 'x'
    sample_user.password_strength = 'x'
    sample_user.global_role_ids = {'x'}
    sample_user.permission_ids = {'x'}

    # -> no changes are recorded, diff is empty
    assert not sample_user.get_updates()
    assert sample_user.to_diff_json() == {}

    # 2) other fields can be updated
    sample_user.email = 'x'
    sample_user.enabled = not sample_user.enabled
    sample_user.first_name = 'x'
    sample_user.last_name = 'x'
    sample_user.display_name = 'x'
    sample_user.tfa_enabled = not sample_user.tfa_enabled
    sample_user.require_password_reset = not sample_user.require_password_reset

    # -> we expect an according number of recorded changes
    assert len(sample_user.get_updates()) == 7

    # -> all changes should be reflected in the diff
    diff_json = sample_user.to_diff_json()
    assert len(diff_json.keys()) == len(sample_user.get_updates())
    for field in sample_user.get_updates():
        json_field = sample_user._parser._obj_to_json[field]
        assert json_field in diff_json
