# Copyright 2018 NTT DATA, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import os
from unittest import mock

import titicaca_store
from oslo_config import cfg

import titicaca.async_.flows.api_image_import as import_flow
import titicaca.async_.flows.plugins.inject_image_metadata as inject_metadata
from titicaca.common import utils
from titicaca import domain
from titicaca import gateway
from titicaca.tests.unit import utils as test_unit_utils
import titicaca.tests.utils as test_utils

CONF = cfg.CONF


UUID1 = 'c80a1a6c-bd1f-41c5-90ee-81afedb1d58d'
TENANT1 = '6838eb7b-6ded-434a-882c-b344c77fe8df'


class TestInjectImageMetadataTask(test_utils.BaseTestCase):

    def setUp(self):
        super(TestInjectImageMetadataTask, self).setUp()

        titicaca_store.register_opts(CONF)
        self.config(default_store='file',
                    stores=['file', 'http'],
                    filesystem_store_datadir=self.test_dir,
                    group="titicaca_store")
        titicaca_store.create_stores(CONF)

        self.work_dir = os.path.join(self.test_dir, 'work_dir')
        utils.safe_mkdirs(self.work_dir)
        self.config(work_dir=self.work_dir, group='task')

        self.context = mock.MagicMock()
        self.img_repo = mock.MagicMock()
        self.task_repo = mock.MagicMock()
        self.image_id = UUID1

        self.gateway = gateway.Gateway()
        self.task_factory = domain.TaskFactory()
        self.img_factory = self.gateway.get_image_factory(self.context)
        self.image = self.img_factory.new_image(image_id=UUID1,
                                                disk_format='qcow2',
                                                container_format='bare',
                                                extra_properties={})
        self.img_repo.get.return_value = self.image

        task_input = {
            "import_from": "http://cloud.foo/image.qcow2",
            "import_from_format": "qcow2",
            "image_properties": {'disk_format': 'qcow2',
                                 'container_format': 'bare'}
        }
        task_ttl = CONF.task.task_time_to_live

        self.task_type = 'import'
        request_id = 'fake_request_id'
        user_id = 'fake_user'
        self.task = self.task_factory.new_task(self.task_type, TENANT1,
                                               UUID1, user_id, request_id,
                                               task_time_to_live=task_ttl,
                                               task_input=task_input)
        self.image.extra_properties = {
            'os_titicaca_import_task': self.task.task_id}
        self.img_repo.get.return_value = self.image
        self.wrapper = import_flow.ImportActionWrapper(self.img_repo,
                                                       self.image_id,
                                                       self.task.task_id)

    def test_inject_image_metadata_using_non_admin_user(self):
        context = test_unit_utils.get_fake_context(roles='member')
        inject_image_metadata = inject_metadata._InjectMetadataProperties(
            context, self.task.task_id, self.task_type, self.wrapper)

        self.config(inject={"test": "abc"},
                    group='inject_metadata_properties')

        inject_image_metadata.execute()
        self.img_repo.save.assert_called_once_with(self.image, 'queued')
        self.assertEqual({"test": "abc",
                          "os_titicaca_import_task": self.task.task_id},
                         self.image.extra_properties)

    def test_inject_image_metadata_using_admin_user(self):
        context = test_unit_utils.get_fake_context(roles='admin')
        inject_image_metadata = inject_metadata._InjectMetadataProperties(
            context, self.task.task_id, self.task_type, self.wrapper)

        self.config(inject={"test": "abc"},
                    group='inject_metadata_properties')

        inject_image_metadata.execute()
        self.img_repo.save.assert_called_once_with(self.image, 'queued')

    def test_inject_image_metadata_empty(self):
        context = test_unit_utils.get_fake_context(roles='member')
        inject_image_metadata = inject_metadata._InjectMetadataProperties(
            context, self.task.task_id, self.task_type, self.wrapper)

        self.config(inject={}, group='inject_metadata_properties')

        inject_image_metadata.execute()
        self.img_repo.save.assert_not_called()
