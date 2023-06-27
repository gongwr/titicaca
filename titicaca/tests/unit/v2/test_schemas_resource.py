# Copyright 2012 OpenStack Foundation.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import titicaca.api.v2.schemas
import titicaca.db.sqlalchemy.api as db_api
import titicaca.tests.unit.utils as unit_test_utils
import titicaca.tests.utils as test_utils


class TestSchemasController(test_utils.BaseTestCase):

    def setUp(self):
        super(TestSchemasController, self).setUp()
        self.controller = titicaca.api.v2.schemas.Controller()

    def test_image(self):
        req = unit_test_utils.get_fake_request()
        output = self.controller.image(req)
        self.assertEqual('image', output['name'])
        expected = set(['status', 'name', 'tags', 'checksum', 'created_at',
                        'disk_format', 'updated_at', 'visibility', 'self',
                        'file', 'container_format', 'schema', 'id', 'size',
                        'direct_url', 'min_ram', 'min_disk', 'protected',
                        'locations', 'owner', 'virtual_size', 'os_hidden',
                        'os_hash_algo', 'os_hash_value', 'stores'])
        self.assertEqual(expected, set(output['properties'].keys()))

    def test_image_has_correct_statuses(self):
        req = unit_test_utils.get_fake_request()
        output = self.controller.image(req)
        self.assertEqual('image', output['name'])
        expected_statuses = set(db_api.STATUSES)
        actual_statuses = set(output['properties']['status']['enum'])
        self.assertEqual(expected_statuses, actual_statuses)

    def test_images(self):
        req = unit_test_utils.get_fake_request()
        output = self.controller.images(req)
        self.assertEqual('images', output['name'])
        expected = set(['images', 'schema', 'first', 'next'])
        self.assertEqual(expected, set(output['properties'].keys()))
        expected = set(['{schema}', '{first}', '{next}'])
        actual = set([link['href'] for link in output['links']])
        self.assertEqual(expected, actual)

    def test_member(self):
        req = unit_test_utils.get_fake_request()
        output = self.controller.member(req)
        self.assertEqual('member', output['name'])
        expected = set(['status', 'created_at', 'updated_at', 'image_id',
                        'member_id', 'schema'])
        self.assertEqual(expected, set(output['properties'].keys()))

    def test_members(self):
        req = unit_test_utils.get_fake_request()
        output = self.controller.members(req)
        self.assertEqual('members', output['name'])
        expected = set(['schema', 'members'])
        self.assertEqual(expected, set(output['properties'].keys()))
