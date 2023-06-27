# Copyright 2015 OpenStack Foundation.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import http.client as http

import titicaca_store
from oslo_log import log as logging
import webob.exc

from titicaca.api import policy
from titicaca.api.v2 import policy as api_policy
from titicaca.common import exception
from titicaca.common import utils
from titicaca.common import wsgi
import titicaca.db
import titicaca.gateway
from titicaca.i18n import _LI
import titicaca.notifier


LOG = logging.getLogger(__name__)


class ImageActionsController(object):
    def __init__(self, db_api=None, policy_enforcer=None, notifier=None,
                 store_api=None):
        self.db_api = db_api or titicaca.db.get_api()
        self.policy = policy_enforcer or policy.Enforcer()
        self.notifier = notifier or titicaca.notifier.Notifier()
        self.store_api = store_api or titicaca_store
        self.gateway = titicaca.gateway.Gateway(self.db_api, self.store_api,
                                              self.notifier, self.policy)

    @utils.mutating
    def deactivate(self, req, image_id):
        image_repo = self.gateway.get_repo(req.context,
                                           authorization_layer=False)
        try:
            # FIXME(danms): This will still enforce the get_image policy
            # which we don't want
            image = image_repo.get(image_id)

            # NOTE(abhishekk): This is the right place to check whether user
            # have permission to deactivate the image and remove the policy
            # check later from the policy layer.
            api_pol = api_policy.ImageAPIPolicy(req.context, image,
                                                self.policy)
            api_pol.deactivate_image()

            status = image.status
            image.deactivate()
            # not necessary to change the status if it's already 'deactivated'
            if status == 'active':
                image_repo.save(image, from_state='active')
            LOG.info(_LI("Image %s is deactivated"), image_id)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.msg)
        except exception.Forbidden as e:
            LOG.debug("User not permitted to deactivate image '%s'", image_id)
            raise webob.exc.HTTPForbidden(explanation=e.msg)
        except exception.InvalidImageStatusTransition as e:
            raise webob.exc.HTTPBadRequest(explanation=e.msg)

    @utils.mutating
    def reactivate(self, req, image_id):
        image_repo = self.gateway.get_repo(req.context,
                                           authorization_layer=False)
        try:
            # FIXME(danms): This will still enforce the get_image policy
            # which we don't want
            image = image_repo.get(image_id)

            # NOTE(abhishekk): This is the right place to check whether user
            # have permission to reactivate the image and remove the policy
            # check later from the policy layer.
            api_pol = api_policy.ImageAPIPolicy(req.context, image,
                                                self.policy)
            api_pol.reactivate_image()

            status = image.status
            image.reactivate()
            # not necessary to change the status if it's already 'active'
            if status == 'deactivated':
                image_repo.save(image, from_state='deactivated')
            LOG.info(_LI("Image %s is reactivated"), image_id)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.msg)
        except exception.Forbidden as e:
            LOG.debug("User not permitted to reactivate image '%s'", image_id)
            raise webob.exc.HTTPForbidden(explanation=e.msg)
        except exception.InvalidImageStatusTransition as e:
            raise webob.exc.HTTPBadRequest(explanation=e.msg)


class ResponseSerializer(wsgi.JSONResponseSerializer):

    def deactivate(self, response, result):
        response.status_int = http.NO_CONTENT

    def reactivate(self, response, result):
        response.status_int = http.NO_CONTENT


def create_resource():
    """Image data resource factory method"""
    deserializer = None
    serializer = ResponseSerializer()
    controller = ImageActionsController()
    return wsgi.Resource(controller, deserializer, serializer)
