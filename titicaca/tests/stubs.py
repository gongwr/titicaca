# Copyright 2010-2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""Stubouts, mocks and fixtures for the test suite"""

import os

try:
    import sendfile
    SENDFILE_SUPPORTED = True
except ImportError:
    SENDFILE_SUPPORTED = False

import routes
import webob

from titicaca.api.middleware import context
from titicaca.api.v2 import router
import titicaca.common.client


DEBUG = False


def stub_out_store_server(stubs, base_dir, **kwargs):
    """Mocks calls to 127.0.0.1 on 9292 for testing.

    Done so that a real Titicaca server does not need to be up and
    running
    """

    class FakeSocket(object):

        def __init__(self, *args, **kwargs):
            pass

        def fileno(self):
            return 42

    class FakeSendFile(object):

        def __init__(self, req):
            self.req = req

        def sendfile(self, o, i, offset, nbytes):
            os.lseek(i, offset, os.SEEK_SET)
            prev_len = len(self.req.body)
            self.req.body += os.read(i, nbytes)
            return len(self.req.body) - prev_len

    class FakeTiticacaConnection(object):

        def __init__(self, *args, **kwargs):
            self.sock = FakeSocket()
            self.stub_force_sendfile = kwargs.get('stub_force_sendfile',
                                                  SENDFILE_SUPPORTED)

        def connect(self):
            return True

        def close(self):
            return True

        def putrequest(self, method, url):
            self.req = webob.Request.blank(url)
            if self.stub_force_sendfile:
                fake_sendfile = FakeSendFile(self.req)
                stubs.Set(sendfile, 'sendfile', fake_sendfile.sendfile)
            self.req.method = method

        def putheader(self, key, value):
            self.req.headers[key] = value

        def endheaders(self):
            hl = [i.lower() for i in self.req.headers.keys()]
            assert not ('content-length' in hl and
                        'transfer-encoding' in hl), (
                'Content-Length and Transfer-Encoding are mutually exclusive')

        def send(self, data):
            # send() is called during chunked-transfer encoding, and
            # data is of the form %x\r\n%s\r\n. Strip off the %x and
            # only write the actual data in tests.
            self.req.body += data.split("\r\n")[1]

        def request(self, method, url, body=None, headers=None):
            self.req = webob.Request.blank(url)
            self.req.method = method
            if headers:
                self.req.headers = headers
            if body:
                self.req.body = body

        def getresponse(self):
            mapper = routes.Mapper()
            api = context.UnauthenticatedContextMiddleware(router.API(mapper))
            res = self.req.get_response(api)

            # httplib.Response has a read() method...fake it out
            def fake_reader():
                return res.body

            setattr(res, 'read', fake_reader)
            return res

    def fake_image_iter(self):
        for i in self.source.app_iter:
            yield i

    def fake_sendable(self, body):
        force = getattr(self, 'stub_force_sendfile', None)
        if force is None:
            return self._stub_orig_sendable(body)
        else:
            if force:
                assert titicaca.common.client.SENDFILE_SUPPORTED
            return force

    setattr(titicaca.common.client.BaseClient, '_stub_orig_sendable',
            titicaca.common.client.BaseClient._sendable)
