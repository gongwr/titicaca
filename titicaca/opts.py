# Copyright (c) 2023 WenRui Gong
# All rights reserved.


__all__ = [
    'list_api_opts',
    'list_manage_opts',
]

import copy
import itertools

from osprofiler import opts as profiler

import titicaca.common.config
import titicaca.common.wsgi


_api_opts = [
    (None, list(itertools.chain(
        titicaca.common.config.common_opts,
        titicaca.common.wsgi.bind_opts,
        titicaca.common.wsgi.eventlet_opts,
        titicaca.common.wsgi.socket_opts,
        titicaca.common.wsgi.store_opts,
        titicaca.common.wsgi.cli_opts))),
    ('task', titicaca.common.config.task_opts),
    profiler.list_opts()[0],
    ('wsgi', titicaca.common.config.wsgi_opts),
]
_manage_opts = [
    (None, [])
]


def list_api_opts():
    """Return a list of oslo_config options available in Titicaca API service.

    Each element of the list is a tuple. The first element is the name of the
    group under which the list of elements in the second element will be
    registered. A group name of None corresponds to the [DEFAULT] group in
    config files.

    This function is also discoverable via the 'titicaca.api' entry point
    under the 'oslo_config.opts' namespace.

    The purpose of this is to allow tools like the Oslo sample config file
    generator to discover the options exposed to users by Titicaca.

    :returns: a list of (group_name, opts) tuples
    """

    return [(g, copy.deepcopy(o)) for g, o in _api_opts]


def list_manage_opts():
    """Return a list of oslo_config options available in Titicaca manage."""
    return [(g, copy.deepcopy(o)) for g, o in _manage_opts]

