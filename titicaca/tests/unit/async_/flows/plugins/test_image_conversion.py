# Copyright 2018 RedHat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import json
import os
import sys
from unittest import mock

import titicaca_store
from oslo_concurrency import processutils
from oslo_config import cfg

import titicaca.async_.flows.api_image_import as import_flow
import titicaca.async_.flows.plugins.image_conversion as image_conversion
from titicaca.async_ import utils as async_utils
from titicaca.common import utils
from titicaca import domain
from titicaca import gateway
import titicaca.tests.utils as test_utils

CONF = cfg.CONF


UUID1 = 'c80a1a6c-bd1f-41c5-90ee-81afedb1d58d'
TENANT1 = '6838eb7b-6ded-434a-882c-b344c77fe8df'


class TestConvertImageTask(test_utils.BaseTestCase):

    def setUp(self):
        super(TestConvertImageTask, self).setUp()

        titicaca_store.register_opts(CONF)
        self.config(default_store='file',
                    stores=['file', 'http'],
                    filesystem_store_datadir=self.test_dir,
                    group="titicaca_store")
        self.config(output_format='qcow2',
                    group='image_conversion')
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
        self.image = self.img_factory.new_image(image_id=self.image_id,
                                                disk_format='raw',
                                                container_format='bare')

        task_input = {
            "import_from": "http://cloud.foo/image.raw",
            "import_from_format": "raw",
            "image_properties": {'disk_format': 'raw',
                                 'container_format': 'bare'}
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

        self.image.extra_properties = {
            'os_titicaca_import_task': self.task.task_id}
        self.wrapper = import_flow.ImportActionWrapper(self.img_repo,
                                                       self.image_id,
                                                       self.task.task_id)

    @mock.patch.object(os, 'stat')
    @mock.patch.object(os, 'remove')
    def test_image_convert_success(self, mock_os_remove, mock_os_stat):
        mock_os_remove.return_value = None
        mock_os_stat.return_value.st_size = 123
        image_convert = image_conversion._ConvertImage(self.context,
                                                       self.task.task_id,
                                                       self.task_type,
                                                       self.wrapper)

        self.task_repo.get.return_value = self.task
        image = mock.MagicMock(image_id=self.image_id, virtual_size=None,
                               extra_properties={
                                   'os_titicaca_import_task': self.task.task_id},
                               disk_format='qcow2')
        self.img_repo.get.return_value = image

        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.return_value = ("", None)
            with mock.patch.object(json, 'loads') as jloads_mock:
                jloads_mock.return_value = {'format': 'raw',
                                            'virtual-size': 456}
                image_convert.execute('file:///test/path.raw')

                # NOTE(hemanthm): Asserting that the source format is passed
                # to qemu-utis to avoid inferring the image format. This
                # shields us from an attack vector described at
                # https://bugs.launchpad.net/titicaca/+bug/1449062/comments/72
                self.assertIn('-f', exc_mock.call_args[0])
                self.assertEqual("qcow2", image.disk_format)

        self.assertEqual('bare', image.container_format)
        self.assertEqual('qcow2', image.disk_format)
        self.assertEqual(456, image.virtual_size)
        self.assertEqual(123, image.size)

    def _setup_image_convert_info_fail(self):
        image_convert = image_conversion._ConvertImage(self.context,
                                                       self.task.task_id,
                                                       self.task_type,
                                                       self.wrapper)

        self.task_repo.get.return_value = self.task
        image = mock.MagicMock(image_id=self.image_id, virtual_size=None,
                               extra_properties={
                                   'os_titicaca_import_task': self.task.task_id},
                               disk_format='qcow2')
        self.img_repo.get.return_value = image
        return image_convert

    def test_image_convert_fails_inspection(self):
        convert = self._setup_image_convert_info_fail()
        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.side_effect = OSError('fail')
            self.assertRaises(OSError,
                              convert.execute, 'file:///test/path.raw')
            exc_mock.assert_called_once_with(
                'qemu-img', 'info',
                '--output=json',
                '/test/path.raw',
                prlimit=async_utils.QEMU_IMG_PROC_LIMITS,
                python_exec=convert.python,
                log_errors=processutils.LOG_ALL_ERRORS)
        # Make sure we did not update the image
        self.img_repo.save.assert_not_called()

    def test_image_convert_inspection_reports_error(self):
        convert = self._setup_image_convert_info_fail()
        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.return_value = '', 'some error'
            self.assertRaises(RuntimeError,
                              convert.execute, 'file:///test/path.raw')
            exc_mock.assert_called_once_with(
                'qemu-img', 'info',
                '--output=json',
                '/test/path.raw',
                prlimit=async_utils.QEMU_IMG_PROC_LIMITS,
                python_exec=convert.python,
                log_errors=processutils.LOG_ALL_ERRORS)
        # Make sure we did not update the image
        self.img_repo.save.assert_not_called()

    def test_image_convert_invalid_qcow(self):
        data = {'format': 'qcow2',
                'backing-filename': '/etc/hosts'}

        convert = self._setup_image_convert_info_fail()
        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.return_value = json.dumps(data), ''
            e = self.assertRaises(RuntimeError,
                                  convert.execute, 'file:///test/path.qcow')
            self.assertEqual('QCOW images with backing files are not allowed',
                             str(e))

    def _test_image_convert_invalid_vmdk(self):
        data = {'format': 'vmdk',
                'format-specific': {
                    'data': {
                        'create-type': 'monolithicFlat',
                    }}}

        convert = self._setup_image_convert_info_fail()
        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.return_value = json.dumps(data), ''
            convert.execute('file:///test/path.vmdk')

    def test_image_convert_invalid_vmdk(self):
        e = self.assertRaises(RuntimeError,
                              self._test_image_convert_invalid_vmdk)
        self.assertEqual('Invalid VMDK create-type specified', str(e))

    def test_image_convert_valid_vmdk_no_types(self):
        with mock.patch.object(CONF.image_format, 'vmdk_allowed_types',
                               new=[]):
            # We make it past the VMDK check and fail because our file
            # does not exist
            e = self.assertRaises(RuntimeError,
                                  self._test_image_convert_invalid_vmdk)
            self.assertEqual('Image is a VMDK, but no VMDK createType is '
                             'specified', str(e))

    def test_image_convert_valid_vmdk(self):
        with mock.patch.object(CONF.image_format, 'vmdk_allowed_types',
                               new=['monolithicSparse', 'monolithicFlat']):
            # We make it past the VMDK check and fail because our file
            # does not exist
            self.assertRaises(FileNotFoundError,
                              self._test_image_convert_invalid_vmdk)

    def test_image_convert_fails(self):
        convert = self._setup_image_convert_info_fail()
        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.side_effect = [('{"format":"raw"}', ''),
                                    OSError('convert_fail')]
            self.assertRaises(OSError,
                              convert.execute, 'file:///test/path.raw')
            exc_mock.assert_has_calls(
                [mock.call('qemu-img', 'info',
                           '--output=json',
                           '/test/path.raw',
                           prlimit=async_utils.QEMU_IMG_PROC_LIMITS,
                           python_exec=convert.python,
                           log_errors=processutils.LOG_ALL_ERRORS),
                 mock.call('qemu-img', 'convert', '-f', 'raw', '-O', 'qcow2',
                           '/test/path.raw', '/test/path.raw.qcow2',
                           log_errors=processutils.LOG_ALL_ERRORS)])
        # Make sure we did not update the image
        self.img_repo.save.assert_not_called()

    def test_image_convert_reports_fail(self):
        convert = self._setup_image_convert_info_fail()
        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.side_effect = [('{"format":"raw"}', ''),
                                    ('', 'some error')]
            self.assertRaises(RuntimeError,
                              convert.execute, 'file:///test/path.raw')
            exc_mock.assert_has_calls(
                [mock.call('qemu-img', 'info',
                           '--output=json',
                           '/test/path.raw',
                           prlimit=async_utils.QEMU_IMG_PROC_LIMITS,
                           python_exec=convert.python,
                           log_errors=processutils.LOG_ALL_ERRORS),
                 mock.call('qemu-img', 'convert', '-f', 'raw', '-O', 'qcow2',
                           '/test/path.raw', '/test/path.raw.qcow2',
                           log_errors=processutils.LOG_ALL_ERRORS)])
        # Make sure we did not update the image
        self.img_repo.save.assert_not_called()

    def test_image_convert_fails_source_format(self):
        convert = self._setup_image_convert_info_fail()
        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.return_value = ('{}', '')
            exc = self.assertRaises(RuntimeError,
                                    convert.execute, 'file:///test/path.raw')
            self.assertIn('Source format not reported', str(exc))
            exc_mock.assert_called_once_with(
                'qemu-img', 'info',
                '--output=json',
                '/test/path.raw',
                prlimit=async_utils.QEMU_IMG_PROC_LIMITS,
                python_exec=convert.python,
                log_errors=processutils.LOG_ALL_ERRORS)
        # Make sure we did not update the image
        self.img_repo.save.assert_not_called()

    def test_image_convert_same_format_does_nothing(self):
        convert = self._setup_image_convert_info_fail()
        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.return_value = (
                '{"format": "qcow2", "virtual-size": 123}', '')
            convert.execute('file:///test/path.qcow')
            # Make sure we only called qemu-img for inspection, not conversion
            exc_mock.assert_called_once_with(
                'qemu-img', 'info',
                '--output=json',
                '/test/path.qcow',
                prlimit=async_utils.QEMU_IMG_PROC_LIMITS,
                python_exec=convert.python,
                log_errors=processutils.LOG_ALL_ERRORS)

        # Make sure we set the virtual_size before we exited
        image = self.img_repo.get.return_value
        self.assertEqual(123, image.virtual_size)

    @mock.patch.object(os, 'remove')
    def test_image_convert_revert_success(self, mock_os_remove):
        mock_os_remove.return_value = None
        image_convert = image_conversion._ConvertImage(self.context,
                                                       self.task.task_id,
                                                       self.task_type,
                                                       self.wrapper)

        self.task_repo.get.return_value = self.task

        with mock.patch.object(processutils, 'execute') as exc_mock:
            exc_mock.return_value = ("", None)
            with mock.patch.object(os.path, 'exists') as os_exists_mock:
                os_exists_mock.return_value = True
                image_convert.revert(result=mock.MagicMock())
                self.assertEqual(1, mock_os_remove.call_count)

    def test_image_convert_interpreter_resolution(self):
        # By default, wsgi.python_interpreter is None, which we should
        # translate to sys.executable at runtime.
        convert = image_conversion._ConvertImage(self.context,
                                                 self.task.task_id,
                                                 self.task_type,
                                                 self.wrapper)
        self.assertEqual(sys.executable, convert.python)

        # If overridden, we should take the interpreter from config.
        fake_interpreter = '/usr/bin/python2.7'
        self.config(python_interpreter=fake_interpreter,
                    group='wsgi')
        convert = image_conversion._ConvertImage(self.context,
                                                 self.task.task_id,
                                                 self.task_type,
                                                 self.wrapper)
        self.assertEqual(fake_interpreter, convert.python)
