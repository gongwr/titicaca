# Copyright 2011 OpenStack Foundation
# Copyright 2012 Red Hat, Inc
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
Utility methods to set testcases up for Swift tests.
"""

import http.client
import http.server
import threading

from oslo_utils import units

FIVE_KB = 5 * units.Ki


class RemoteImageHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        """
        Respond to an image HEAD request fake metadata
        """
        if 'images' in self.path:
            self.send_response(http.client.OK)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', FIVE_KB)
            self.end_headers()
            return
        else:
            self.send_error(
                http.client.NOT_FOUND, 'File Not Found: %s' % self.path,
            )
            return

    def do_GET(self):
        """
        Respond to an image GET request with fake image content.
        """
        if 'images' in self.path:
            self.send_response(http.client.OK)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', FIVE_KB)
            self.end_headers()
            image_data = b'*' * FIVE_KB
            self.wfile.write(image_data)
            self.wfile.close()
            return
        else:
            self.send_error(
                http.client.NOT_FOUND, 'File Not Found: %s' % self.path,
            )
            return

    def log_message(self, format, *args):
        """
        Simple override to prevent writing crap to stderr...
        """
        pass


def setup_http(test):
    server_class = http.server.HTTPServer
    remote_server = server_class(('127.0.0.1', 0), RemoteImageHandler)
    remote_ip, remote_port = remote_server.server_address

    def serve_requests(httpd):
        httpd.serve_forever()

    threading.Thread(target=serve_requests, args=(remote_server,)).start()
    test.http_server = remote_server
    test.http_ip = remote_ip
    test.http_port = remote_port
    test.addCleanup(test.http_server.shutdown)


def get_http_uri(test, image_id):
    uri = ('http://%(http_ip)s:%(http_port)d/images/' %
           {'http_ip': test.http_ip, 'http_port': test.http_port})
    uri += image_id
    return uri
