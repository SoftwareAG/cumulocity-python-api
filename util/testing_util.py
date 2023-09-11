# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

import os
import random
import re

from requests import request


def read_webcontent(source_url, target_path):
    """Read web content to a local file."""
    response = request('get', source_url)
    if 200 <= response.status_code <= 299:
        with open(target_path, 'wt', encoding='utf-8') as file:
            file.write(response.text)
    else:
        raise RuntimeError('Unable to read web content. Unexpected response from web site: '
                           f'HTTP {response.status_code} {response.text}')

class RandomNameGenerator:
    """Provides randomly generated names using a public service."""

    wordlist_path = 'wordlist.txt'
    wordlist_url = 'https://raw.githubusercontent.com/mike-hearn/useapassphrase/master/js/wordlist.js'
    if not os.path.exists(wordlist_path):
        read_webcontent(wordlist_url, wordlist_path)
    with open(wordlist_path, 'rt', encoding='utf-8') as file:
        file.readline()  # skip first line
        lines = file.readlines()
    words = [re.sub('[^\\w]', '', line) for line in lines]

    @classmethod
    def random_name(cls, num: int = 3, sep: str = '_') -> str:
        """Generate a readable random name from joined random words.

        Args:
            num (int):  number of random words to concactenate
            sep (str):  concatenation separator

        Returns:
            The generated name
        """
        words = [random.choice(cls.words) for _ in range(0, num)]
        return sep.join(words)
