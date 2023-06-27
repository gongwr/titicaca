# Copyright 2015 Hewlett Packard
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""Tests healthcheck middleware."""

import http.client
import tempfile

import httplib2

from titicaca.tests import functional
from titicaca.tests import utils


class HealthcheckMiddlewareTest(functional.FunctionalTest):

    def request(self):
        url = 'http://127.0.0.1:%s/healthcheck' % self.api_port
        http = httplib2.Http()
        return http.request(url, 'GET')

    @utils.skip_if_disabled
    def test_healthcheck_enabled(self):
        self.cleanup()
        self.start_servers(**self.__dict__.copy())

        response, content = self.request()
        self.assertEqual(b'OK', content)
        self.assertEqual(http.client.OK, response.status)

        self.stop_servers()

    def test_healthcheck_disabled(self):
        with tempfile.NamedTemporaryFile() as test_disable_file:
            self.cleanup()
            self.api_server.disable_path = test_disable_file.name
            self.start_servers(**self.__dict__.copy())

            response, content = self.request()
            self.assertEqual(b'DISABLED BY FILE', content)
            self.assertEqual(http.client.SERVICE_UNAVAILABLE, response.status)

            self.stop_servers()
