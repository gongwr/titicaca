# Copyright (c) 2023 WenRui Gong
# All rights reserved.


import itertools

from titicaca.policies import base
from titicaca.policies import metadef
from titicaca.policies import tasks


def list_rules():
    return itertools.chain(
        base.list_rules(),
        tasks.list_rules(),
        metadef.list_rules(),
    )
