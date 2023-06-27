# Copyright 2015 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import json
from unittest import mock

import titicaca_store
from oslo_concurrency import processutils
from oslo_config import cfg

from titicaca.async_.flows import introspect
from titicaca.async_ import utils as async_utils
from titicaca import domain
import titicaca.tests.utils as test_utils

CONF = cfg.CONF

UUID1 = 'c80a1a6c-bd1f-41c5-90ee-81afedb1d58d'
TENANT1 = '6838eb7b-6ded-434a-882c-b344c77fe8df'


class TestImportTask(test_utils.BaseTestCase):

    def setUp(self):
        super(TestImportTask, self).setUp()
        self.task_factory = domain.TaskFactory()
        task_input = {
            "import_from": "http://cloud.foo/image.qcow2",
            "import_from_format": "qcow2",
            "image_properties": mock.sentinel.image_properties
        }
        task_ttl = CONF.task.task_time_to_live

        self.task_type = 'import'
        image_id = 'fake_image_id'
        user_id = 'fake_user'
        request_id = 'fake_request_id'
        self.task = self.task_factory.new_task(self.task_type, TENANT1,
                                               image_id, user_id, request_id,
                                               task_time_to_live=task_ttl,
                                               task_input=task_input)

        self.context = mock.Mock()
        self.img_repo = mock.Mock()
        self.task_repo = mock.Mock()
        self.img_factory = mock.Mock()

        titicaca_store.register_opts(CONF)
        self.config(default_store='file',
                    stores=['file', 'http'],
                    filesystem_store_datadir=self.test_dir,
                    group="titicaca_store")
        titicaca_store.create_stores(CONF)

    def test_introspect_success(self):
        image_create = introspect._Introspect(self.task.task_id,
                                              self.task_type,
                                              self.img_repo)

        self.task_repo.get.return_value = self.task
        image_id = mock.sentinel.image_id
        image = mock.MagicMock(image_id=image_id)
        self.img_repo.get.return_value = image

        with mock.patch.object(processutils, 'execute') as exc_mock:
            result = json.dumps({
                "virtual-size": 10737418240,
                "filename": "/tmp/image.qcow2",
                "cluster-size": 65536,
                "format": "qcow2",
                "actual-size": 373030912,
                "format-specific": {
                    "type": "qcow2",
                    "data": {
                        "compat": "0.10"
                    }
                },
                "dirty-flag": False
            })

            exc_mock.return_value = (result, None)
            image_create.execute(image, '/test/path.qcow2')
            self.assertEqual(10737418240, image.virtual_size)

            # NOTE(hemanthm): Assert that process limits are being applied on
            # "qemu-img info" calls. See bug #1449062 for more details.
            kw_args = exc_mock.call_args[1]
            self.assertIn('prlimit', kw_args)
            self.assertEqual(async_utils.QEMU_IMG_PROC_LIMITS,
                             kw_args.get('prlimit'))

    def test_introspect_no_image(self):
        image_create = introspect._Introspect(self.task.task_id,
                                              self.task_type,
                                              self.img_repo)

        self.task_repo.get.return_value = self.task
        image_id = mock.sentinel.image_id
        image = mock.MagicMock(image_id=image_id, virtual_size=None)
        self.img_repo.get.return_value = image

        # NOTE(flaper87): Don't mock, test the error.
        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.return_value = (None, "some error")
            # NOTE(flaper87): Pls, read the `OptionalTask._catch_all`
            # docs to know why this is commented.
            # self.assertRaises(RuntimeError,
            #                  image_create.execute,
            #                  image, '/test/path.qcow2')
            image_create.execute(image, '/test/path.qcow2')
            self.assertIsNone(image.virtual_size)
