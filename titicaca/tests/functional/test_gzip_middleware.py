# Copyright 2013 Red Hat, Inc
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""Tests gzip middleware."""

import httplib2

from titicaca.tests import functional
from titicaca.tests import utils


class GzipMiddlewareTest(functional.FunctionalTest):

    @utils.skip_if_disabled
    def test_gzip_requests(self):
        self.cleanup()
        self.start_servers(**self.__dict__.copy())

        def request(path, headers=None):
            # We don't care what version we're using here so,
            # sticking with latest
            url = 'http://127.0.0.1:%s/v2/%s' % (self.api_port, path)
            http = httplib2.Http()
            return http.request(url, 'GET', headers=headers)

        # Accept-Encoding: Identity
        headers = {'Accept-Encoding': 'identity'}
        response, content = request('images', headers=headers)
        self.assertIsNone(response.get("-content-encoding"))

        # Accept-Encoding: gzip
        headers = {'Accept-Encoding': 'gzip'}
        response, content = request('images', headers=headers)
        self.assertEqual('gzip', response.get("-content-encoding"))

        self.stop_servers()
