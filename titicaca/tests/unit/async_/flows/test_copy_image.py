# Copyright 2020 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import datetime
import os
from unittest import mock

import titicaca_store as store_api
from oslo_config import cfg

from titicaca.async_.flows._internal_plugins import copy_image
from titicaca.async_.flows import api_image_import
import titicaca.common.exception as exception
from titicaca import domain
import titicaca.tests.unit.utils as unit_test_utils
import titicaca.tests.utils as test_utils

CONF = cfg.CONF

DATETIME = datetime.datetime(2012, 5, 16, 15, 27, 36, 325355)


TENANT1 = '6838eb7b-6ded-434a-882c-b344c77fe8df'
UUID1 = 'c80a1a6c-bd1f-41c5-90ee-81afedb1d58d'
FAKEHASHALGO = 'fake-name-for-sha512'
CHKSUM = '93264c3edf5972c9f1cb309543d38a5c'
RESERVED_STORES = {
    'os_titicaca_staging_store': 'file',
}


def _db_fixture(id, **kwargs):
    obj = {
        'id': id,
        'name': None,
        'visibility': 'shared',
        'properties': {},
        'checksum': None,
        'os_hash_algo': FAKEHASHALGO,
        'os_hash_value': None,
        'owner': None,
        'status': 'queued',
        'tags': [],
        'size': None,
        'virtual_size': None,
        'locations': [],
        'protected': False,
        'disk_format': None,
        'container_format': None,
        'deleted': False,
        'min_ram': None,
        'min_disk': None,
    }
    obj.update(kwargs)
    return obj


class TestCopyImageTask(test_utils.BaseTestCase):

    def setUp(self):
        super(TestCopyImageTask, self).setUp()

        self.db = unit_test_utils.FakeDB(initialize=False)
        self._create_images()
        self.image_repo = mock.MagicMock()
        self.task_repo = mock.MagicMock()
        self.image_id = UUID1
        self.staging_store = mock.MagicMock()
        self.task_factory = domain.TaskFactory()

        task_input = {
            "import_req": {
                'method': {
                    'name': 'copy-image',
                },
                'stores': ['fast']
            }
        }
        task_ttl = CONF.task.task_time_to_live

        self.task_type = 'import'
        request_id = 'fake_request_id'
        user_id = 'fake_user'
        self.task = self.task_factory.new_task(self.task_type, TENANT1,
                                               self.image_id, user_id,
                                               request_id,
                                               task_time_to_live=task_ttl,
                                               task_input=task_input)
        self.task_id = self.task.task_id
        self.action_wrapper = api_image_import.ImportActionWrapper(
            self.image_repo, self.image_id, self.task_id)
        self.image_repo.get.return_value = mock.MagicMock(
            extra_properties={'os_titicaca_import_task': self.task_id})

        stores = {'cheap': 'file', 'fast': 'file'}
        self.config(enabled_backends=stores)
        store_api.register_store_opts(CONF, reserved_stores=RESERVED_STORES)
        self.config(default_backend='fast', group='titicaca_store')
        store_api.create_multi_stores(CONF, reserved_stores=RESERVED_STORES)

    def _create_images(self):
        self.images = [
            _db_fixture(UUID1, owner=TENANT1, checksum=CHKSUM,
                        name='1', size=512, virtual_size=2048,
                        visibility='public',
                        disk_format='raw',
                        container_format='bare',
                        status='active',
                        tags=['redhat', '64bit', 'power'],
                        properties={'hypervisor_type': 'kvm', 'foo': 'bar',
                                    'bar': 'foo'},
                        locations=[{'url': 'file://%s/%s' % (self.test_dir,
                                                             UUID1),
                                    'metadata': {'store': 'fast'},
                                    'status': 'active'}],
                        created_at=DATETIME + datetime.timedelta(seconds=1)),
        ]
        [self.db.image_create(None, image) for image in self.images]

        self.db.image_tag_set_all(None, UUID1, ['ping', 'pong'])

    @mock.patch.object(store_api, 'get_store_from_store_identifier')
    def test_copy_image_to_staging_store(self, mock_store_api):
        mock_store_api.return_value = self.staging_store
        copy_image_task = copy_image._CopyImage(
            self.task.task_id, self.task_type, self.image_repo,
            self.action_wrapper)
        with mock.patch.object(self.image_repo, 'get') as get_mock:
            get_mock.return_value = mock.MagicMock(
                image_id=self.images[0]['id'],
                locations=self.images[0]['locations'],
                extra_properties={'os_titicaca_import_task': self.task.task_id},
                status=self.images[0]['status']
            )
            with mock.patch.object(store_api, 'get') as get_data:
                get_data.return_value = (b"dddd", 4)
                copy_image_task.execute()
                self.staging_store.add.assert_called_once()
                mock_store_api.assert_called_once_with(
                    "os_titicaca_staging_store")

    @mock.patch.object(os, 'unlink')
    @mock.patch.object(os.path, 'getsize')
    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(store_api, 'get_store_from_store_identifier')
    def test_copy_image_to_staging_store_partial_data_exists(
            self, mock_store_api, mock_exists, mock_getsize, mock_unlink):
        mock_store_api.return_value = self.staging_store
        mock_exists.return_value = True
        mock_getsize.return_value = 3

        copy_image_task = copy_image._CopyImage(
            self.task.task_id, self.task_type, self.image_repo,
            self.action_wrapper)
        with mock.patch.object(self.image_repo, 'get') as get_mock:
            get_mock.return_value = mock.MagicMock(
                image_id=self.images[0]['id'],
                locations=self.images[0]['locations'],
                status=self.images[0]['status'],
                extra_properties={'os_titicaca_import_task': self.task.task_id},
                size=4
            )
            with mock.patch.object(store_api, 'get') as get_data:
                get_data.return_value = (b"dddd", 4)
                copy_image_task.execute()
                mock_exists.assert_called_once()
                mock_getsize.assert_called_once()
                mock_unlink.assert_called_once()
                self.staging_store.add.assert_called_once()
                mock_store_api.assert_called_once_with(
                    "os_titicaca_staging_store")

    @mock.patch.object(os, 'unlink')
    @mock.patch.object(os.path, 'getsize')
    @mock.patch.object(os.path, 'exists')
    @mock.patch.object(store_api, 'get_store_from_store_identifier')
    def test_copy_image_to_staging_store_data_exists(
            self, mock_store_api, mock_exists, mock_getsize, mock_unlink):
        mock_store_api.return_value = self.staging_store
        mock_exists.return_value = True
        mock_getsize.return_value = 4

        copy_image_task = copy_image._CopyImage(
            self.task.task_id, self.task_type, self.image_repo,
            self.action_wrapper)
        with mock.patch.object(self.image_repo, 'get') as get_mock:
            get_mock.return_value = mock.MagicMock(
                image_id=self.images[0]['id'],
                locations=self.images[0]['locations'],
                status=self.images[0]['status'],
                extra_properties={'os_titicaca_import_task': self.task.task_id},
                size=4
            )
            copy_image_task.execute()
            mock_exists.assert_called_once()
            mock_store_api.assert_called_once_with(
                "os_titicaca_staging_store")
            mock_getsize.assert_called_once()
            # As valid image data already exists in staging area
            # it does not remove it and also does not download
            # it again to staging area
            mock_unlink.assert_not_called()
            self.staging_store.add.assert_not_called()

    @mock.patch.object(store_api, 'get_store_from_store_identifier')
    def test_copy_non_existing_image_to_staging_store_(self, mock_store_api):
        mock_store_api.return_value = self.staging_store
        copy_image_task = copy_image._CopyImage(
            self.task.task_id, self.task_type, self.image_repo,
            self.action_wrapper)
        with mock.patch.object(self.image_repo, 'get') as get_mock:
            get_mock.side_effect = exception.NotFound()

            self.assertRaises(exception.NotFound, copy_image_task.execute)
            mock_store_api.assert_called_once_with(
                "os_titicaca_staging_store")
