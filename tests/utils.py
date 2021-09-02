# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

import random
import re
from typing import List, Set

import pytest
from requests import request

from c8y_api.model._base import CumulocityObject  # noqa


def get_ids(objs: List[CumulocityObject]) -> Set[str]:
    """Isolate the ID from a list of database objects."""
    return {o.id for o in objs}


@pytest.fixture(scope='function')
def random_name() -> str:
    """Provide a random name."""
    return RandomNameGenerator.random_name()


def read_webcontent(source_url, target_path):
    response = request('get', source_url)
    if 200 <= response.status_code <= 299:
        with open(target_path, 'w') as file:
            file.write(response.text)
    else:
        raise RuntimeError('Unable to read web content. Unexpected response from web site: '
                           f'HTTP {response.status_code} {response.text}')


class RandomNameGenerator:
    """Provides randomly generated names using a public service."""

    wordlist_path = 'wordlist.txt'
    read_webcontent('https://raw.githubusercontent.com/mike-hearn/useapassphrase/master/js/wordlist.js',
                    wordlist_path)
    with open(wordlist_path) as file:
        file.readline()  # skip first line
        lines = file.readlines()
    words = [re.sub('[^\\w]', '', line) for line in lines]

    @classmethod
    def random_name(cls, num: int = 3, sep: str = '_') -> str:
        words = [random.choice(cls.words) for _ in range(0, num)]
        return sep.join(words)
