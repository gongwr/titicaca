# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import io
import sys
from unittest import mock

import titicaca_store as store
from oslo_config import cfg
from oslo_log import log as logging

import titicaca.cmd.api
import titicaca.cmd.cache_cleaner
import titicaca.cmd.cache_pruner
import titicaca.common.config
from titicaca.common import exception as exc
import titicaca.common.wsgi
import titicaca.image_cache.cleaner
from titicaca.image_cache import prefetcher
import titicaca.image_cache.pruner
from titicaca.tests import utils as test_utils


CONF = cfg.CONF


class TestTiticacaApiCmd(test_utils.BaseTestCase):

    __argv_backup = None

    def _do_nothing(self, *args, **kwargs):
        pass

    def _raise(self, exc):
        def fake(*args, **kwargs):
            raise exc
        return fake

    def setUp(self):
        super(TestTiticacaApiCmd, self).setUp()
        self.__argv_backup = sys.argv
        sys.argv = ['titicaca-api']
        self.stderr = io.StringIO()
        sys.stderr = self.stderr

        store.register_opts(CONF)

        self.mock_object(titicaca.common.config, 'load_paste_app',
                         self._do_nothing)
        self.mock_object(titicaca.common.wsgi.Server, 'start',
                         self._do_nothing)
        self.mock_object(titicaca.common.wsgi.Server, 'wait',
                         self._do_nothing)

    def tearDown(self):
        sys.stderr = sys.__stderr__
        sys.argv = self.__argv_backup
        super(TestTiticacaApiCmd, self).tearDown()

    @mock.patch('titicaca.async_.set_threadpool_model',)
    @mock.patch.object(prefetcher, 'Prefetcher')
    def test_supported_default_store(self, mock_prefetcher, mock_set_model):
        self.config(group='titicaca_store', default_store='file')
        titicaca.cmd.api.main()
        # Make sure we declared the system threadpool model as eventlet
        mock_set_model.assert_called_once_with('eventlet')

    @mock.patch.object(prefetcher, 'Prefetcher')
    @mock.patch('titicaca.async_.set_threadpool_model', new=mock.MagicMock())
    def test_worker_creation_failure(self, mock_prefetcher):
        failure = exc.WorkerCreationFailure(reason='test')
        self.mock_object(titicaca.common.wsgi.Server, 'start',
                         self._raise(failure))
        exit = self.assertRaises(SystemExit, titicaca.cmd.api.main)
        self.assertEqual(2, exit.code)

    @mock.patch.object(titicaca.common.config, 'parse_cache_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch.object(titicaca.image_cache.ImageCache, 'init_driver')
    @mock.patch.object(titicaca.image_cache.ImageCache, 'clean')
    def test_cache_cleaner_main(self, mock_cache_clean,
                                mock_cache_init_driver, mock_log_setup,
                                mock_parse_config):
        mock_cache_init_driver.return_value = None

        manager = mock.MagicMock()
        manager.attach_mock(mock_log_setup, 'mock_log_setup')
        manager.attach_mock(mock_parse_config, 'mock_parse_config')
        manager.attach_mock(mock_cache_init_driver, 'mock_cache_init_driver')
        manager.attach_mock(mock_cache_clean, 'mock_cache_clean')
        titicaca.cmd.cache_cleaner.main()
        expected_call_sequence = [mock.call.mock_parse_config(),
                                  mock.call.mock_log_setup(CONF, 'titicaca'),
                                  mock.call.mock_cache_init_driver(),
                                  mock.call.mock_cache_clean()]
        self.assertEqual(expected_call_sequence, manager.mock_calls)

    @mock.patch.object(titicaca.image_cache.base.CacheApp, '__init__')
    def test_cache_cleaner_main_runtime_exception_handling(self, mock_cache):
        mock_cache.return_value = None
        self.mock_object(titicaca.image_cache.cleaner.Cleaner, 'run',
                         self._raise(RuntimeError))
        exit = self.assertRaises(SystemExit, titicaca.cmd.cache_cleaner.main)
        self.assertEqual('ERROR: ', exit.code)

    @mock.patch.object(titicaca.common.config, 'parse_cache_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch.object(titicaca.image_cache.ImageCache, 'init_driver')
    @mock.patch.object(titicaca.image_cache.ImageCache, 'prune')
    def test_cache_pruner_main(self, mock_cache_prune,
                               mock_cache_init_driver, mock_log_setup,
                               mock_parse_config):
        mock_cache_init_driver.return_value = None

        manager = mock.MagicMock()
        manager.attach_mock(mock_log_setup, 'mock_log_setup')
        manager.attach_mock(mock_parse_config, 'mock_parse_config')
        manager.attach_mock(mock_cache_init_driver, 'mock_cache_init_driver')
        manager.attach_mock(mock_cache_prune, 'mock_cache_prune')
        titicaca.cmd.cache_pruner.main()
        expected_call_sequence = [mock.call.mock_parse_config(),
                                  mock.call.mock_log_setup(CONF, 'titicaca'),
                                  mock.call.mock_cache_init_driver(),
                                  mock.call.mock_cache_prune()]
        self.assertEqual(expected_call_sequence, manager.mock_calls)

    @mock.patch.object(titicaca.image_cache.base.CacheApp, '__init__')
    def test_cache_pruner_main_runtime_exception_handling(self, mock_cache):
        mock_cache.return_value = None
        self.mock_object(titicaca.image_cache.pruner.Pruner, 'run',
                         self._raise(RuntimeError))
        exit = self.assertRaises(SystemExit, titicaca.cmd.cache_pruner.main)
        self.assertEqual('ERROR: ', exit.code)

    def test_fail_with_value_error(self):
        with mock.patch('sys.stderr.write') as mock_stderr:
            with mock.patch('sys.exit') as mock_exit:
                exc_msg = 'A ValueError, LOL!'
                exc = ValueError(exc_msg)
                titicaca.cmd.api.fail(exc)
                mock_stderr.assert_called_once_with('ERROR: %s\n' % exc_msg)
                mock_exit.assert_called_once_with(4)

    def test_fail_with_config_exception(self):
        with mock.patch('sys.stderr.write') as mock_stderr:
            with mock.patch('sys.exit') as mock_exit:
                exc_msg = 'A ConfigError by George!'
                exc = cfg.ConfigFileValueError(exc_msg)
                titicaca.cmd.api.fail(exc)
                mock_stderr.assert_called_once_with('ERROR: %s\n' % exc_msg)
                mock_exit.assert_called_once_with(5)

    def test_fail_with_unknown_exception(self):
        with mock.patch('sys.stderr.write') as mock_stderr:
            with mock.patch('sys.exit') as mock_exit:
                exc_msg = 'A Crazy Unknown Error.'
                exc = CrayCray(exc_msg)
                titicaca.cmd.api.fail(exc)
                mock_stderr.assert_called_once_with('ERROR: %s\n' % exc_msg)
                mock_exit.assert_called_once_with(99)

    def test_main_with_store_config_exception(self):
        with mock.patch.object(titicaca.common.config,
                               'parse_args') as mock_config:
            with mock.patch('sys.exit') as mock_exit:
                exc = store.exceptions.BadStoreConfiguration()
                mock_config.side_effect = exc
                titicaca.cmd.api.main()
                mock_exit.assert_called_once_with(3)

    def test_main_with_runtime_error(self):
        with mock.patch.object(titicaca.common.config,
                               'parse_args') as mock_config:
            with mock.patch('sys.exit') as mock_exit:
                exc = RuntimeError()
                mock_config.side_effect = exc
                titicaca.cmd.api.main()
                mock_exit.assert_called_once_with(1)

    def test_main_with_worker_creation_failure(self):
        with mock.patch.object(titicaca.common.config,
                               'parse_args') as mock_config:
            with mock.patch('sys.exit') as mock_exit:
                exx = exc.WorkerCreationFailure()
                mock_config.side_effect = exx
                titicaca.cmd.api.main()
                mock_exit.assert_called_once_with(2)


class CrayCray(Exception):
    pass
