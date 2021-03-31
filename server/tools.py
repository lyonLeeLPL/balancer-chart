import datetime
import time
import os
import sys

# from decimal import *
import decimal

import numpy as np
import pandas as pd

from dateutil import relativedelta
from dateutil.parser import parse as parse_date
from pytz import timezone

# for re-export
import logging

decimal.getcontext().prec = 5

# =============================================
# check min, python version
if sys.version_info < (3, 8):
    raise SystemError("Requires Python version >= 3.8")
# =============================================


class make_object:
    """ create object from dict """

    def __init__(self, **entries):
        self.__dict__.update(entries)

# ---------------------------------------------


def createLogger(name, level=logging.WARNING):
    """:Return: a logger with the given `name` and optional `level`."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def read_single_argv(param, default=None):
    args = " ".join(sys.argv).strip().split(param)
    if len(args) > 1:
        args = args[1].strip().split(" ")[0]
        return args if "-" not in args else None
    return default
