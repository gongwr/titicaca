# Copyright (c) 2014 OpenStack Foundation.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

__all__ = [
    'list_api_opts',
    'list_scrubber_opts',
    'list_cache_opts',
    'list_manage_opts',
    'list_image_import_opts',
]

import copy
import itertools

from osprofiler import opts as profiler

import titicaca.api.middleware.context
import titicaca.api.versions
import titicaca.async_.flows._internal_plugins
import titicaca.async_.flows.api_image_import
import titicaca.async_.flows.convert
from titicaca.async_.flows.plugins import plugin_opts
import titicaca.async_.taskflow_executor
import titicaca.common.config
import titicaca.common.location_strategy
import titicaca.common.location_strategy.store_type
import titicaca.common.property_utils
import titicaca.common.wsgi
import titicaca.image_cache
import titicaca.image_cache.drivers.sqlite
import titicaca.notifier
import titicaca.scrubber


_api_opts = [
    (None, list(itertools.chain(
        titicaca.api.middleware.context.context_opts,
        titicaca.api.versions.versions_opts,
        titicaca.common.config.common_opts,
        titicaca.common.location_strategy.location_strategy_opts,
        titicaca.common.property_utils.property_opts,
        titicaca.common.wsgi.bind_opts,
        titicaca.common.wsgi.eventlet_opts,
        titicaca.common.wsgi.socket_opts,
        titicaca.common.wsgi.wsgi_opts,
        titicaca.common.wsgi.store_opts,
        titicaca.common.wsgi.cache_opts,
        titicaca.common.wsgi.cli_opts,
        titicaca.image_cache.drivers.sqlite.sqlite_opts,
        titicaca.image_cache.image_cache_opts,
        titicaca.notifier.notifier_opts,
        titicaca.scrubber.scrubber_opts))),
    ('image_format', titicaca.common.config.image_format_opts),
    ('task', titicaca.common.config.task_opts),
    ('taskflow_executor', list(itertools.chain(
        titicaca.async_.taskflow_executor.taskflow_executor_opts,
        titicaca.async_.flows.convert.convert_task_opts))),
    ('store_type_location_strategy',
     titicaca.common.location_strategy.store_type.store_type_opts),
    profiler.list_opts()[0],
    ('paste_deploy', titicaca.common.config.paste_deploy_opts),
    ('wsgi', titicaca.common.config.wsgi_opts),
]
_scrubber_opts = [
    (None, list(itertools.chain(
        titicaca.common.config.common_opts,
        titicaca.scrubber.scrubber_opts,
        titicaca.scrubber.scrubber_cmd_opts,
        titicaca.scrubber.scrubber_cmd_cli_opts))),
]
_cache_opts = [
    (None, list(itertools.chain(
        titicaca.common.config.common_opts,
        titicaca.image_cache.drivers.sqlite.sqlite_opts,
        titicaca.image_cache.image_cache_opts))),
]
_manage_opts = [
    (None, [])
]
_image_import_opts = [
    ('image_import_opts',
     titicaca.async_.flows.api_image_import.api_import_opts),
    ('import_filtering_opts',
     titicaca.async_.flows._internal_plugins.import_filtering_opts),
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


def list_scrubber_opts():
    """Return a list of oslo_config options available in Titicaca Scrubber
    service.
    """
    return [(g, copy.deepcopy(o)) for g, o in _scrubber_opts]


def list_cache_opts():
    """Return a list of oslo_config options available in Titicaca Cache
    service.
    """
    return [(g, copy.deepcopy(o)) for g, o in _cache_opts]


def list_manage_opts():
    """Return a list of oslo_config options available in Titicaca manage."""
    return [(g, copy.deepcopy(o)) for g, o in _manage_opts]


def list_image_import_opts():
    """Return a list of oslo_config options available for Image Import"""

    opts = copy.deepcopy(_image_import_opts)
    opts.extend(plugin_opts.get_plugin_opts())
    return [(g, copy.deepcopy(o)) for g, o in opts]
