# Copyright 2011-2013 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.
import titicaca_store
from unittest import mock

from titicaca.common import exception
from titicaca.common import store_utils
import titicaca.location
from titicaca.tests.unit import base


CONF = {'default_store': 'file',
        'swift_store_auth_address': 'localhost:8080',
        'swift_store_container': 'titicaca',
        'swift_store_user': 'user',
        'swift_store_key': 'key',
        'default_swift_reference': 'store_1'
        }


class TestStoreLocation(base.StoreClearingUnitTest):

    class FakeImageProxy(object):
        size = None
        context = None
        store_api = mock.Mock()
        store_utils = store_utils

    def test_add_location_for_image_without_size(self):

        def fake_get_size_from_backend(uri, context=None):
            return 1

        self.mock_object(titicaca_store, 'get_size_from_backend',
                         fake_get_size_from_backend)

        with mock.patch('titicaca.location._check_image_location'):
            loc1 = {'url': 'file:///fake1.img.tar.gz', 'metadata': {}}
            loc2 = {'url': 'file:///fake2.img.tar.gz', 'metadata': {}}

            # Test for insert location
            image1 = TestStoreLocation.FakeImageProxy()
            locations = titicaca.location.StoreLocations(image1, [])
            locations.insert(0, loc2)
            self.assertEqual(1, image1.size)

            # Test for set_attr of _locations_proxy
            image2 = TestStoreLocation.FakeImageProxy()
            locations = titicaca.location.StoreLocations(image2, [loc1])
            locations[0] = loc2
            self.assertIn(loc2, locations)
            self.assertEqual(1, image2.size)

    def test_add_location_with_restricted_sources(self):

        loc1 = {'url': 'file:///fake1.img.tar.gz', 'metadata': {}}
        loc2 = {'url': 'swift+config:///xxx', 'metadata': {}}
        loc3 = {'url': 'filesystem:///foo.img.tar.gz', 'metadata': {}}

        # Test for insert location
        image1 = TestStoreLocation.FakeImageProxy()
        locations = titicaca.location.StoreLocations(image1, [])
        self.assertRaises(exception.BadStoreUri, locations.insert, 0, loc1)
        self.assertRaises(exception.BadStoreUri, locations.insert, 0, loc3)
        self.assertNotIn(loc1, locations)
        self.assertNotIn(loc3, locations)

        # Test for set_attr of _locations_proxy
        image2 = TestStoreLocation.FakeImageProxy()
        locations = titicaca.location.StoreLocations(image2, [loc1])
        self.assertRaises(exception.BadStoreUri, locations.insert, 0, loc2)
        self.assertNotIn(loc2, locations)
