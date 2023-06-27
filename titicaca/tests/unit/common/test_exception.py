# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import http.client as http

from oslo_utils import encodeutils

from titicaca.common import exception
from titicaca.tests import utils as test_utils


class TiticacaExceptionTestCase(test_utils.BaseTestCase):

    def test_default_error_msg(self):
        class FakeTiticacaException(exception.TiticacaException):
            message = "default message"

        exc = FakeTiticacaException()
        self.assertEqual('default message',
                         encodeutils.exception_to_unicode(exc))

    def test_specified_error_msg(self):
        msg = exception.TiticacaException('test')
        self.assertIn('test', encodeutils.exception_to_unicode(msg))

    def test_default_error_msg_with_kwargs(self):
        class FakeTiticacaException(exception.TiticacaException):
            message = "default message: %(code)s"

        exc = FakeTiticacaException(code=int(http.INTERNAL_SERVER_ERROR))
        self.assertEqual("default message: 500",
                         encodeutils.exception_to_unicode(exc))

    def test_specified_error_msg_with_kwargs(self):
        msg = exception.TiticacaException('test: %(code)s',
                                        code=int(http.INTERNAL_SERVER_ERROR))
        self.assertIn('test: 500', encodeutils.exception_to_unicode(msg))

    def test_non_unicode_error_msg(self):
        exc = exception.TiticacaException('test')
        self.assertIsInstance(encodeutils.exception_to_unicode(exc), str)
