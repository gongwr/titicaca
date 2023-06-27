# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
Image Cache Management API
"""

from oslo_log import log as logging
import routes

from titicaca.api.v2 import cached_images
from titicaca.common import wsgi
from titicaca.i18n import _LI

LOG = logging.getLogger(__name__)


class CacheManageFilter(wsgi.Middleware):
    def __init__(self, app):
        mapper = routes.Mapper()
        resource = cached_images.create_resource()

        mapper.connect("/v2/cached_images",
                       controller=resource,
                       action="get_cached_images",
                       conditions=dict(method=["GET"]))

        mapper.connect("/v2/cached_images/{image_id}",
                       controller=resource,
                       action="delete_cached_image",
                       conditions=dict(method=["DELETE"]))

        mapper.connect("/v2/cached_images",
                       controller=resource,
                       action="delete_cached_images",
                       conditions=dict(method=["DELETE"]))

        mapper.connect("/v2/queued_images/{image_id}",
                       controller=resource,
                       action="queue_image",
                       conditions=dict(method=["PUT"]))

        mapper.connect("/v2/queued_images",
                       controller=resource,
                       action="get_queued_images",
                       conditions=dict(method=["GET"]))

        mapper.connect("/v2/queued_images/{image_id}",
                       controller=resource,
                       action="delete_queued_image",
                       conditions=dict(method=["DELETE"]))

        mapper.connect("/v2/queued_images",
                       controller=resource,
                       action="delete_queued_images",
                       conditions=dict(method=["DELETE"]))

        self._mapper = mapper
        self._resource = resource

        LOG.info(_LI("Initialized image cache management middleware"))
        super(CacheManageFilter, self).__init__(app)

    def process_request(self, request):
        # Map request to our resource object if we can handle it
        match = self._mapper.match(request.path_info, request.environ)
        if match:
            request.environ['wsgiorg.routing_args'] = (None, match)
            return self._resource(request)
        # Pass off downstream if we don't match the request path
        else:
            return None
