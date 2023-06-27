# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.
import http.client as http

import titicaca_store
from oslo_log import log as logging
from oslo_utils import encodeutils
import webob.exc

from titicaca.api import policy
from titicaca.api.v2 import images as v2_api
from titicaca.api.v2 import policy as api_policy
from titicaca.common import exception
from titicaca.common import utils
from titicaca.common import wsgi
import titicaca.db
import titicaca.gateway
from titicaca.i18n import _
import titicaca.notifier


LOG = logging.getLogger(__name__)


class Controller(object):
    def __init__(self, db_api=None, policy_enforcer=None, notifier=None,
                 store_api=None):
        self.db_api = db_api or titicaca.db.get_api()
        self.policy = policy_enforcer or policy.Enforcer()
        self.notifier = notifier or titicaca.notifier.Notifier()
        self.store_api = store_api or titicaca_store
        self.gateway = titicaca.gateway.Gateway(self.db_api, self.store_api,
                                              self.notifier, self.policy)

    @utils.mutating
    def update(self, req, image_id, tag_value):
        image_repo = self.gateway.get_repo(
            req.context, authorization_layer=False)
        try:
            image = image_repo.get(image_id)
            api_policy.ImageAPIPolicy(req.context, image,
                                      self.policy).modify_image()
            image.tags.add(tag_value)
            image_repo.save(image)
        except exception.NotFound:
            msg = _("Image %s not found.") % image_id
            LOG.warning(msg)
            raise webob.exc.HTTPNotFound(explanation=msg)
        except exception.Forbidden:
            msg = _("Not allowed to update tags for image %s.") % image_id
            LOG.warning(msg)
            raise webob.exc.HTTPForbidden(explanation=msg)
        except exception.Invalid as e:
            msg = (_("Could not update image: %s")
                   % encodeutils.exception_to_unicode(e))
            LOG.warning(msg)
            raise webob.exc.HTTPBadRequest(explanation=msg)
        except exception.ImageTagLimitExceeded as e:
            msg = (_("Image tag limit exceeded for image %(id)s: %(e)s:")
                   % {"id": image_id,
                      "e": encodeutils.exception_to_unicode(e)})
            LOG.warning(msg)
            raise webob.exc.HTTPRequestEntityTooLarge(explanation=msg)

    @utils.mutating
    def delete(self, req, image_id, tag_value):
        image_repo = self.gateway.get_repo(
            req.context, authorization_layer=False)
        try:
            image = image_repo.get(image_id)
            api_policy.ImageAPIPolicy(req.context, image,
                                      self.policy).modify_image()

            if tag_value not in image.tags:
                raise webob.exc.HTTPNotFound()
            image.tags.remove(tag_value)
            image_repo.save(image)
        except exception.NotFound:
            msg = _("Image %s not found.") % image_id
            LOG.warning(msg)
            raise webob.exc.HTTPNotFound(explanation=msg)
        except exception.Forbidden:
            msg = _("Not allowed to delete tags for image %s.") % image_id
            LOG.warning(msg)
            raise webob.exc.HTTPForbidden(explanation=msg)


class ResponseSerializer(wsgi.JSONResponseSerializer):
    def update(self, response, result):
        response.status_int = http.NO_CONTENT

    def delete(self, response, result):
        response.status_int = http.NO_CONTENT


class RequestDeserializer(wsgi.JSONRequestDeserializer):
    def update(self, request):
        try:
            schema = v2_api.get_schema()
            schema_format = {"tags": [request.urlvars.get('tag_value')]}
            schema.validate(schema_format)
        except exception.InvalidObject as e:
            raise webob.exc.HTTPBadRequest(explanation=e.msg)
        return super(RequestDeserializer, self).default(request)


def create_resource():
    """Images resource factory method"""
    serializer = ResponseSerializer()
    deserializer = RequestDeserializer()
    controller = Controller()
    return wsgi.Resource(controller, deserializer, serializer)
