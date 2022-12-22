# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

import inspect
import os

import dotenv


def load_dotenv(sample_name: str | None = None):
    """Load environment variables from .env files.

    This function will look for two files within the working directory:
    A general `.env` file and a sample specific .env-{sample_name} file
    which has higher priority.
    """
    # load general .env
    dotenv.load_dotenv()
    # check and load sample .env
    if not sample_name:
        caller_file = inspect.stack()[1].filename
        sample_name = os.path.splitext(os.path.split(caller_file)[1])[0]

    sample_env = f'.env-{sample_name}'
    if os.path.exists(sample_env):
        print(f"Found custom .env extension: {sample_env}")
        with open(sample_env, 'r', encoding='UTF-8') as f:
            dotenv.load_dotenv(stream=f)
