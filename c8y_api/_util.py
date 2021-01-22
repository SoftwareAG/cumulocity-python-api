# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import logging
import json

__LOG_FORMAT = '%(levelname).1s %(asctime)s %(name)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=__LOG_FORMAT)


def log(lvl, msg, *args):
    tuples, no_tuples = [], []
    for a in args:
        tuples.append(a) if isinstance(a, tuple) else no_tuples.append(a)
    if tuples:
        msg = format_properties(msg, *tuples)
    logging.log(lvl, msg, *no_tuples)


def error(msg, *args):
    log(logging.ERROR, msg, *args)


def warning(msg, *args):
    log(logging.WARNING, msg, *args)


def info(msg, *args):
    log(logging.INFO, msg, *args)


def debug(msg, *args):
    log(logging.DEBUG, msg, *args)


def format_properties(message, *extensions):
    """Format a log message with several properties."""
    for extension in extensions:
        name = extension[0]
        value = extension[1]
        if value is dict:
            value = json.dumps(value)
        if value is not str:
            value = str(value)
        message += f"\n     {name}: {value}"
    return message
