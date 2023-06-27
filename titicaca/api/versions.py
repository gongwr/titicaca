# Copyright 2012 OpenStack Foundation.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import http.client
import urllib

from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils
import webob.dec

from titicaca.common import wsgi
from titicaca.i18n import _


versions_opts = [
    cfg.StrOpt('public_endpoint',
               help=_("""
Public url endpoint to use for Titicaca versions response.

This is the public url endpoint that will appear in the Titicaca
"versions" response. If no value is specified, the endpoint that is
displayed in the version's response is that of the host running the
API service. Change the endpoint to represent the proxy URL if the
API service is running behind a proxy. If the service is running
behind a load balancer, add the load balancer's URL for this value.

Possible values:
    * None
    * Proxy URL
    * Load balancer URL

Related options:
    * None

""")),
]

CONF = cfg.CONF
CONF.register_opts(versions_opts)

LOG = logging.getLogger(__name__)


class Controller(object):

    """A wsgi controller that reports which API versions are supported."""

    def index(self, req, explicit=False):
        """Respond to a request for all OpenStack API versions."""
        def build_version_object(version, path, status):
            url = CONF.public_endpoint or req.application_url
            # Always add '/' to url end for urljoin href url
            url = url.rstrip('/') + '/'
            href = urllib.parse.urljoin(url, path).rstrip('/') + '/'
            return {
                'id': 'v%s' % version,
                'status': status,
                'links': [
                    {
                        'rel': 'self',
                        'href': '%s' % href,
                    },
                ],
            }

        version_objs = []
        if CONF.image_cache_dir:
            version_objs.extend([
                build_version_object(2.16, 'v2', 'CURRENT'),
                build_version_object(2.15, 'v2', 'SUPPORTED'),
                build_version_object(2.14, 'v2', 'SUPPORTED'),
            ])
        else:
            version_objs.extend([
                build_version_object(2.15, 'v2', 'CURRENT'),
            ])
        if CONF.enabled_backends:
            version_objs.extend([
                build_version_object(2.13, 'v2', 'SUPPORTED'),
                build_version_object(2.12, 'v2', 'SUPPORTED'),
                build_version_object(2.11, 'v2', 'SUPPORTED'),
                build_version_object('2.10', 'v2', 'SUPPORTED'),
                build_version_object(2.9, 'v2', 'SUPPORTED'),
                build_version_object(2.8, 'v2', 'SUPPORTED'),
            ])
        else:
            version_objs.extend([
                build_version_object(2.9, 'v2', 'SUPPORTED'),
            ])
        version_objs.extend([
            build_version_object(2.7, 'v2', 'SUPPORTED'),
            build_version_object(2.6, 'v2', 'SUPPORTED'),
            build_version_object(2.5, 'v2', 'SUPPORTED'),
            build_version_object(2.4, 'v2', 'SUPPORTED'),
            build_version_object(2.3, 'v2', 'SUPPORTED'),
            build_version_object(2.2, 'v2', 'SUPPORTED'),
            build_version_object(2.1, 'v2', 'SUPPORTED'),
            build_version_object(2.0, 'v2', 'SUPPORTED'),
        ])

        status = explicit and http.client.OK or http.client.MULTIPLE_CHOICES
        response = webob.Response(request=req,
                                  status=status,
                                  content_type='application/json')
        response.body = jsonutils.dump_as_bytes(dict(versions=version_objs))
        return response

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        return self.index(req)


def create_resource(conf):
    return wsgi.Resource(Controller())
