# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
Titicaca Image Cache Invalid Cache Entry and Stalled Image cleaner

This is meant to be run as a periodic task from cron.

If something goes wrong while we're caching an image (for example the fetch
times out, or an exception is raised), we create an 'invalid' entry. These
entries are left around for debugging purposes. However, after some period of
time, we want to clean these up.

Also, if an incomplete image hangs around past the image_cache_stall_time
period, we automatically sweep it up.
"""

import os
import sys

from oslo_log import log as logging

# If ../titicaca/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'titicaca', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from titicaca.common import config
from titicaca.image_cache import cleaner

CONF = config.CONF
logging.register_options(CONF)
CONF.set_default(name='use_stderr', default=True)


def main():
    try:
        config.parse_cache_args()
        logging.setup(CONF, 'titicaca')

        app = cleaner.Cleaner()
        app.run()
    except RuntimeError as e:
        sys.exit("ERROR: %s" % e)
