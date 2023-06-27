# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""Functional test case that tests logging output"""

import http.client as http
import os
import stat

import httplib2

from titicaca.tests import functional


class TestLogging(functional.FunctionalTest):

    """Functional tests for Titicaca's logging output"""

    def test_debug(self):
        """
        Test logging output proper when debug is on.
        """
        self.cleanup()
        self.start_servers()

        # The default functional test case has both debug on. Let's verify
        # that debug statements appear in the API logs.

        self.assertTrue(os.path.exists(self.api_server.log_file))

        with open(self.api_server.log_file, 'r') as f:
            api_log_out = f.read()

        self.assertIn('DEBUG titicaca', api_log_out)

        self.stop_servers()

    def test_no_debug(self):
        """
        Test logging output proper when debug is off.
        """
        self.cleanup()
        self.start_servers(debug=False)

        self.assertTrue(os.path.exists(self.api_server.log_file))

        with open(self.api_server.log_file, 'r') as f:
            api_log_out = f.read()

        self.assertNotIn('DEBUG titicaca', api_log_out)
        self.stop_servers()

    def assertNotEmptyFile(self, path):
        self.assertTrue(os.path.exists(path))
        self.assertNotEqual(os.stat(path)[stat.ST_SIZE], 0)

    def test_logrotate(self):
        """
        Test that we notice when our log file has been rotated
        """

        # Moving in-use files is not supported on Windows.
        # The log handler itself may be configured to rotate files.
        if os.name == 'nt':
            raise self.skipException("Unsupported platform.")

        self.cleanup()
        self.start_servers()

        self.assertNotEmptyFile(self.api_server.log_file)

        os.rename(self.api_server.log_file, self.api_server.log_file + ".1")

        path = "http://%s:%d/" % ("127.0.0.1", self.api_port)
        response, content = httplib2.Http().request(path, 'GET')
        self.assertEqual(http.MULTIPLE_CHOICES, response.status)

        self.assertNotEmptyFile(self.api_server.log_file)

        self.stop_servers()
