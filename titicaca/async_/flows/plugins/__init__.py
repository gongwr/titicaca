# Copyright 2017 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from oslo_config import cfg
from stevedore import named


CONF = cfg.CONF


def get_import_plugins(**kwargs):
    task_list = CONF.image_import_opts.image_import_plugins
    extensions = named.NamedExtensionManager('titicaca.image_import.plugins',
                                             names=task_list,
                                             name_order=True,
                                             invoke_on_load=True,
                                             invoke_kwds=kwargs)
    for extension in extensions.extensions:
        yield extension.obj
