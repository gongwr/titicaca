# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import testtools
from unittest import mock
import webob

import titicaca.api.common
from titicaca.common import exception


class SimpleIterator(object):
    def __init__(self, file_object, chunk_size):
        self.file_object = file_object
        self.chunk_size = chunk_size

    def __iter__(self):
        def read_chunk():
            return self.fobj.read(self.chunk_size)

        chunk = read_chunk()
        while chunk:
            yield chunk
            chunk = read_chunk()
        else:
            return


class TestSizeCheckedIter(testtools.TestCase):
    def _get_image_metadata(self):
        return {'id': 'e31cb99c-fe89-49fb-9cc5-f5104fffa636'}

    def _get_webob_response(self):
        request = webob.Request.blank('/')
        response = webob.Response()
        response.request = request
        return response

    def test_uniform_chunk_size(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = titicaca.api.common.size_checked_iter(
            resp, meta, 4, ['AB', 'CD'], None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertRaises(StopIteration, next, checked_image)

    def test_small_last_chunk(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = titicaca.api.common.size_checked_iter(
            resp, meta, 3, ['AB', 'C'], None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('C', next(checked_image))
        self.assertRaises(StopIteration, next, checked_image)

    def test_variable_chunk_size(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = titicaca.api.common.size_checked_iter(
            resp, meta, 6, ['AB', '', 'CDE', 'F'], None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('', next(checked_image))
        self.assertEqual('CDE', next(checked_image))
        self.assertEqual('F', next(checked_image))
        self.assertRaises(StopIteration, next, checked_image)

    def test_too_many_chunks(self):
        """An image should streamed regardless of expected_size"""
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = titicaca.api.common.size_checked_iter(
            resp, meta, 4, ['AB', 'CD', 'EF'], None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertEqual('EF', next(checked_image))
        self.assertRaises(exception.TiticacaException, next, checked_image)

    def test_too_few_chunks(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = titicaca.api.common.size_checked_iter(resp, meta, 6,
                                                            ['AB', 'CD'],
                                                            None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertRaises(exception.TiticacaException, next, checked_image)

    def test_too_much_data(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = titicaca.api.common.size_checked_iter(resp, meta, 3,
                                                            ['AB', 'CD'],
                                                            None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertRaises(exception.TiticacaException, next, checked_image)

    def test_too_little_data(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = titicaca.api.common.size_checked_iter(resp, meta, 6,
                                                            ['AB', 'CD', 'E'],
                                                            None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertEqual('E', next(checked_image))
        self.assertRaises(exception.TiticacaException, next, checked_image)


class TestThreadPool(testtools.TestCase):
    @mock.patch('titicaca.async_.get_threadpool_model')
    def test_get_thread_pool(self, mock_gtm):
        get_thread_pool = titicaca.api.common.get_thread_pool

        pool1 = get_thread_pool('pool1', size=123)
        get_thread_pool('pool2', size=456)
        pool1a = get_thread_pool('pool1')

        # Two calls for the same pool should return the exact same thing
        self.assertEqual(pool1, pool1a)

        # Only two calls to get new threadpools should have been made
        mock_gtm.return_value.assert_has_calls(
            [mock.call(123), mock.call(456)])

    @mock.patch('titicaca.async_.get_threadpool_model')
    def test_get_thread_pool_log(self, mock_gtm):
        with mock.patch.object(titicaca.api.common, 'LOG') as mock_log:
            titicaca.api.common.get_thread_pool('test-pool')
            mock_log.debug.assert_called_once_with(
                'Initializing named threadpool %r', 'test-pool')
