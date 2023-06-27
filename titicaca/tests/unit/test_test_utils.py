# Copyright 2020 Red Hat, Inc
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from titicaca.tests import utils as test_utils


class TestFakeData(test_utils.BaseTestCase):
    def test_via_read(self):
        fd = test_utils.FakeData(1024)
        data = []
        for i in range(0, 1025, 256):
            chunk = fd.read(256)
            data.append(chunk)
            if not chunk:
                break

        self.assertEqual(5, len(data))
        # Make sure we got a zero-length final read
        self.assertEqual(b'', data[-1])
        # Make sure we only got 1024 bytes
        self.assertEqual(1024, len(b''.join(data)))

    def test_via_iter(self):
        data = b''.join(list(test_utils.FakeData(1024)))
        self.assertEqual(1024, len(data))
