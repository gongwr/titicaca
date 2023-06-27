# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.


"""
Cleans up any invalid cache entries
"""

from titicaca.image_cache import base


class Cleaner(base.CacheApp):

    def run(self):
        self.cache.clean()
