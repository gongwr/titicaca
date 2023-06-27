# Copyright 2012 Red Hat, Inc.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from titicaca.image_cache import ImageCache


class CacheApp(object):

    def __init__(self):
        self.cache = ImageCache()
