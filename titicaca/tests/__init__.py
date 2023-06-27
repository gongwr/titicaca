# Copyright 2010-2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import builtins
import os

import eventlet
# NOTE(jokke): As per the eventlet commit
# b756447bab51046dfc6f1e0e299cc997ab343701 there's circular import happening
# which can be solved making sure the hubs are properly and fully imported
# before calling monkey_patch(). This is solved in eventlet 0.22.0 but we
# need to address it before that is widely used around.
eventlet.hubs.get_hub()

if os.name == 'nt':
    # eventlet monkey patching the os module causes subprocess.Popen to fail
    # on Windows when using pipes due to missing non-blocking IO support.
    eventlet.patcher.monkey_patch(os=False)
else:
    eventlet.patcher.monkey_patch()

import titicaca.async_
# NOTE(danms): Default to eventlet threading for tests
titicaca.async_.set_threadpool_model('eventlet')

# See http://code.google.com/p/python-nose/issues/detail?id=373
# The code below enables tests to work with i18n _() blocks
setattr(builtins, '_', lambda x: x)

# Set up logging to output debugging
import logging
logger = logging.getLogger()
hdlr = logging.FileHandler('run_tests.log', 'w')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)
