#!/usr/bin/env python

# Copyright 2011-2012 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
Titicaca Image Cache Pre-fetcher

This is meant to be run from the command line after queueing
images to be pretched.
"""

import os
import sys

# If ../titicaca/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'titicaca', '__init__.py')):
    sys.path.insert(0, possible_topdir)

import titicaca_store
from oslo_log import log as logging

from titicaca.common import config
from titicaca.image_cache import prefetcher

CONF = config.CONF
logging.register_options(CONF)
CONF.set_default(name='use_stderr', default=True)


def main():
    try:
        config.parse_cache_args()
        logging.setup(CONF, 'titicaca')
        CONF.import_opt('enabled_backends', 'titicaca.common.wsgi')

        if CONF.enabled_backends:
            titicaca_store.register_store_opts(CONF)
            titicaca_store.create_multi_stores(CONF)
            titicaca_store.verify_store()
        else:
            titicaca_store.register_opts(CONF)
            titicaca_store.create_stores(CONF)
            titicaca_store.verify_default_store()

        app = prefetcher.Prefetcher()
        app.run()
    except RuntimeError as e:
        sys.exit("ERROR: %s" % e)


if __name__ == '__main__':
    main()
