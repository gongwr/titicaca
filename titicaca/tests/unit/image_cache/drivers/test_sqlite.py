# Copyright (c) 2017 Huawei Technologies Co., Ltd.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
Tests for the sqlite image_cache driver.
"""

import os
from unittest import mock

import ddt

from titicaca.image_cache.drivers import sqlite
from titicaca.tests import utils


@ddt.ddt
class TestSqlite(utils.BaseTestCase):

    @ddt.data(True, False)
    def test_delete_cached_file(self, throw_not_exists):

        with mock.patch.object(os, 'unlink') as mock_unlink:
            if throw_not_exists:
                mock_unlink.side_effect = OSError((2, 'File not found'))

        # Should not raise an exception in all cases
        sqlite.delete_cached_file('/tmp/dummy_file')
