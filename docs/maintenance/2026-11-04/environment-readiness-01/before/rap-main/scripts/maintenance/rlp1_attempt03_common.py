"""Attempt03 fixes scalar trace copying and unique failure bookkeeping only."""
from rlp1_common import *
import rlp1_common as _base
ENG = B/'engineering-preflight/attempt-03'


def finish(name,passed=True):
    return _base.finish('attempt03_'+name,passed)


def fail(name,ex):
    return _base.fail('attempt03_'+name,ex)
