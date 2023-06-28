#!/usr/bin/env python

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
Titicaca API Server
"""

import os
import sys

from oslo_reports import guru_meditation_report as gmr
from oslo_utils import encodeutils

# If ../titicaca/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
BASE_PATH = os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir, os.pardir))
if os.path.exists(os.path.join(BASE_PATH, 'titicaca', '__init__.py')):
    sys.path.insert(0, BASE_PATH)

from oslo_config import cfg
from oslo_log import log as logging
import osprofiler.initializer

from titicaca.common import config
from titicaca.common import exception
from titicaca.common import wsgi
from titicaca import version

CONF = cfg.CONF
CONF.import_group("profiler", "titicaca.common.wsgi")
logging.register_options(CONF)
wsgi.register_cli_opts()

# NOTE(rosmaita): Any new exceptions added should preserve the current
# error codes for backward compatibility.  The value 99 is returned
# for errors not listed in this map.
ERROR_CODE_MAP = {RuntimeError: 1,
                  exception.WorkerCreationFailure: 2,
                  ValueError: 3,
                  cfg.ConfigFileValueError: 4}


def fail(e):
    sys.stderr.write("ERROR: %s\n" % encodeutils.exception_to_unicode(e))
    return_code = ERROR_CODE_MAP.get(type(e), 99)
    sys.exit(return_code)


def main():
    try:
        config.parse_args()
        config.set_config_defaults()
        logging.setup(CONF, 'titicaca')
        gmr.TextGuruMeditation.setup_autorun(version)

        if CONF.profiler.enabled:
            osprofiler.initializer.init_from_conf(
                conf=CONF,
                context={},
                project="titicaca",
                service="api",
                host=CONF.bind_host
            )

        if CONF.enforce_secure_rbac != CONF.oslo_policy.enforce_new_defaults:
            fail_message = (
                "[DEFAULT] enforce_secure_rbac does not match "
                "[oslo_policy] enforce_new_defaults. Please set both to "
                "True to enable secure RBAC personas. Otherwise, make sure "
                "both are False.")
            raise exception.ServerError(fail_message)

    except Exception as e:
        fail(e)


if __name__ == '__main__':
    main()
