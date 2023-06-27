# Copyright 2012 Red Hat, Inc
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""Functional test cases for sqlite-specific logic"""


from titicaca.tests import functional
from titicaca.tests.utils import depends_on_exe
from titicaca.tests.utils import execute
from titicaca.tests.utils import skip_if_disabled


class TestSqlite(functional.FunctionalTest):
    """Functional tests for sqlite-specific logic"""

    @depends_on_exe('sqlite3')
    @skip_if_disabled
    def test_big_int_mapping(self):
        """Ensure BigInteger not mapped to BIGINT"""
        self.cleanup()
        self.start_servers(**self.__dict__.copy())

        cmd = 'sqlite3 tests.sqlite ".schema"'
        exitcode, out, err = execute(cmd, raise_error=True)

        self.assertNotIn('BIGINT', out)

        self.stop_servers()
