# Copyright 2020 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from titicaca.common import wsgi


def init(mapper):
    reject_resource = wsgi.Resource(wsgi.RejectMethodController())
    mapper.connect("/v1", controller=reject_resource,
                   action="reject")


class API(wsgi.Router):
    """WSGI entry point for satisfy grenade."""

    def __init__(self, mapper):
        mapper = mapper or wsgi.APIMapper()

        init(mapper)

        super(API, self).__init__(mapper)
