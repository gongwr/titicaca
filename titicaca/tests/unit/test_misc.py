# Copyright 2010-2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import os

from titicaca.common import crypt
from titicaca.common import utils
from titicaca.tests import utils as test_utils


class UtilsTestCase(test_utils.BaseTestCase):

    def test_encryption(self):
        # Check that original plaintext and unencrypted ciphertext match
        # Check keys of the three allowed lengths
        key_list = ["1234567890abcdef",
                    "12345678901234567890abcd",
                    "1234567890abcdef1234567890ABCDEF"]
        plaintext_list = ['']
        blocksize = 64
        for i in range(3 * blocksize):
            text = os.urandom(i).decode('latin1')
            plaintext_list.append(text)

        for key in key_list:
            for plaintext in plaintext_list:
                ciphertext = crypt.urlsafe_encrypt(key, plaintext, blocksize)
                self.assertIsInstance(ciphertext, str)
                self.assertNotEqual(ciphertext, plaintext)
                text = crypt.urlsafe_decrypt(key, ciphertext)
                self.assertIsInstance(text, str)
                self.assertEqual(plaintext, text)

    def test_empty_metadata_headers(self):
        """Ensure unset metadata is not encoded in HTTP headers"""

        metadata = {
            'foo': 'bar',
            'snafu': None,
            'bells': 'whistles',
            'unset': None,
            'empty': '',
            'properties': {
                'distro': '',
                'arch': None,
                'user': 'nobody',
            },
        }

        headers = utils.image_meta_to_http_headers(metadata)

        self.assertNotIn('x-image-meta-snafu', headers)
        self.assertNotIn('x-image-meta-uset', headers)
        self.assertNotIn('x-image-meta-snafu', headers)
        self.assertNotIn('x-image-meta-property-arch', headers)

        self.assertEqual('bar', headers.get('x-image-meta-foo'))
        self.assertEqual('whistles', headers.get('x-image-meta-bells'))
        self.assertEqual('', headers.get('x-image-meta-empty'))
        self.assertEqual('', headers.get('x-image-meta-property-distro'))
        self.assertEqual('nobody', headers.get('x-image-meta-property-user'))
