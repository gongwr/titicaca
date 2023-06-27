# Copyright 2020 Red Hat, Inc
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.
from titicaca.i18n import _
from oslo_config import cfg

removed_opts = [
    cfg.BoolOpt('owner_is_tenant',
                default=True,
                help=_("""
This option has been removed in Wallaby.  Because there is no migration path
for installations that had owner_is_tenant==False, we have defined this option
so that the code can probe the config file and refuse to start the api service
if the deployment has been using that setting.
""")),
]


def register_removed_options():
    # NOTE(cyril): This should only be called when we need to use options that
    # have been removed and are therefore no longer relevant. This is the case
    # of upgrade checks, for instance.
    cfg.CONF.register_opts(removed_opts)
