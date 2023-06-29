# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2010 OpenStack Foundation
# Copyright 2014 IBM Corp.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Utility methods for working with WSGI servers
"""

import os

import webob.dec
import webob.exc
from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging
from osprofiler import opts as profiler_opts

from titicaca import i18n
from titicaca.i18n import _

bind_opts = [
    cfg.HostAddressOpt('bind_host',
                       default='0.0.0.0',
                       help=_("""
IP address to bind the titicaca servers to.

Provide an IP address to bind the titicaca server to. The default
value is ``0.0.0.0``.

Edit this option to enable the server to listen on one particular
IP address on the network card. This facilitates selection of a
particular network interface for the server.

Possible values:
    * A valid IPv4 address
    * A valid IPv6 address

Related options:
    * None

""")),

    cfg.PortOpt('bind_port',
                help=_("""
Port number on which the server will listen.

Provide a valid port number to bind the server's socket to. This
port is then set to identify processes and forward network messages
that arrive at the server. The default bind_port value for the API
server is 9292 and for the registry server is 9191.

Possible values:
    * A valid port number (0 to 65535)

Related options:
    * None

""")),
]

socket_opts = [
    cfg.IntOpt('backlog',
               default=4096,
               min=1,
               help=_("""
Set the number of incoming connection requests.

Provide a positive integer value to limit the number of requests in
the backlog queue. The default queue size is 4096.

An incoming connection to a TCP listener socket is queued before a
connection can be established with the server. Setting the backlog
for a TCP socket ensures a limited queue size for incoming traffic.

Possible values:
    * Positive integer

Related options:
    * None

""")),

    cfg.IntOpt('tcp_keepidle',
               default=600,
               min=1,
               help=_("""
Set the wait time before a connection recheck.

Provide a positive integer value representing time in seconds which
is set as the idle wait time before a TCP keep alive packet can be
sent to the host. The default value is 600 seconds.

Setting ``tcp_keepidle`` helps verify at regular intervals that a
connection is intact and prevents frequent TCP connection
reestablishment.

Possible values:
    * Positive integer value representing time in seconds

Related options:
    * None

""")),
]

eventlet_opts = [
    cfg.IntOpt('workers',
               min=0,
               help=_("""
Number of Titicaca worker processes to start.

Provide a non-negative integer value to set the number of child
process workers to service requests. By default, the number of CPUs
available is set as the value for ``workers`` limited to 8. For
example if the processor count is 6, 6 workers will be used, if the
processor count is 24 only 8 workers will be used. The limit will only
apply to the default value, if 24 workers is configured, 24 is used.

Each worker process is made to listen on the port set in the
configuration file and contains a greenthread pool of size 1000.

NOTE: Setting the number of workers to zero, triggers the creation
of a single API process with a greenthread pool of size 1000.

Possible values:
    * 0
    * Positive integer value (typically equal to the number of CPUs)

Related options:
    * None

""")),

    cfg.IntOpt('max_header_line',
               default=16384,
               min=0,
               help=_("""
Maximum line size of message headers.

Provide an integer value representing a length to limit the size of
message headers. The default value is 16384.

NOTE: ``max_header_line`` may need to be increased when using large
tokens (typically those generated by the Titicaca v3 API with big
service catalogs). However, it is to be kept in mind that larger
values for ``max_header_line`` would flood the logs.

Setting ``max_header_line`` to 0 sets no limit for the line size of
message headers.

Possible values:
    * 0
    * Positive integer

Related options:
    * None

""")),

    cfg.BoolOpt('http_keepalive',
                default=True,
                help=_("""
Set keep alive option for HTTP over TCP.

Provide a boolean value to determine sending of keep alive packets.
If set to ``False``, the server returns the header
"Connection: close". If set to ``True``, the server returns a
"Connection: Keep-Alive" in its responses. This enables retention of
the same TCP connection for HTTP conversations instead of opening a
new one with each new request.

This option must be set to ``False`` if the client socket connection
needs to be closed explicitly after the response is received and
read successfully by the client.

Possible values:
    * True
    * False

Related options:
    * None

""")),

    cfg.IntOpt('client_socket_timeout',
               default=900,
               min=0,
               help=_("""
Timeout for client connections' socket operations.

Provide a valid integer value representing time in seconds to set
the period of wait before an incoming connection can be closed. The
default value is 900 seconds.

The value zero implies wait forever.

Possible values:
    * Zero
    * Positive integer

Related options:
    * None

""")),
]

wsgi_opts = [
    cfg.StrOpt('secure_proxy_ssl_header',
               deprecated_for_removal=True,
               deprecated_reason=_('Use the http_proxy_to_wsgi middleware '
                                   'instead.'),
               help=_('The HTTP header used to determine the scheme for the '
                      'original request, even if it was removed by an SSL '
                      'terminating proxy. Typical value is '
                      '"HTTP_X_FORWARDED_PROTO".')),
]

store_opts = [
    cfg.DictOpt('enabled_backends',
                help=_('Key:Value pair of store identifier and store type. '
                       'In case of multiple backends should be separated '
                       'using comma.')),
]

cli_opts = [
    cfg.StrOpt('pipe-handle',
               help='This argument is used internally on Windows. Titicaca '
                    'passes a pipe handle to child processes, which is then '
                    'used for inter-process communication.'),
]

cache_opts = [
    cfg.FloatOpt('cache_prefetcher_interval',
                 default=300,
                 help=_("""
The interval in seconds to run periodic job cache_images.

The cache_images method will fetch all images which are in queued state
for caching in cache directory. The default value is 300.

Possible values:
    * Positive integer

Related options:
    * None
"""))
]

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.register_opts(bind_opts)
CONF.register_opts(socket_opts)
CONF.register_opts(eventlet_opts)
CONF.register_opts(wsgi_opts)
CONF.register_opts(store_opts)
CONF.register_opts(cache_opts)
profiler_opts.set_defaults(CONF)


def register_cli_opts():
    CONF.register_cli_opts(cli_opts)


def get_num_workers():
    """Return the configured number of workers."""

    # Windows only: we're already running on the worker side.
    if os.name == 'nt' and getattr(CONF, 'pipe_handle', None):
        return 0

    if CONF.workers is None:
        # None implies the number of CPUs limited to 8
        # See Launchpad bug #1748916 and the config help text
        workers = processutils.get_worker_count()
        return workers if workers < 8 else 8
    return CONF.workers


def translate_exception(req, e):
    """Translates all translatable elements of the given exception."""

    # The RequestClass attribute in the webob.dec.wsgify decorator
    # does not guarantee that the request object will be a particular
    # type; this check is therefore necessary.
    if not hasattr(req, "best_match_language"):
        return e

    locale = req.best_match_language()

    if isinstance(e, webob.exc.HTTPError):
        e.explanation = i18n.translate(e.explanation, locale)
        e.detail = i18n.translate(e.detail, locale)
        if getattr(e, 'body_template', None):
            e.body_template = i18n.translate(e.body_template, locale)
    return e
