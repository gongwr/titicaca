# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
Prunes the Image Cache
"""

from titicaca.image_cache import base


class Pruner(base.CacheApp):

    def run(self):
        self.cache.prune()
