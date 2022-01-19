# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

import os
from typing import Set


def c8y_keys() -> Set[str]:
    """Provide the names of defined Cumulocity environment variables.

    Returns: A set of environment variable names, starting with 'C8Y_'
    """
    return set(filter(lambda x: 'C8Y_' in x, os.environ.keys()))
