# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from oslo_db.sqlalchemy import test_fixtures

import titicaca.tests.functional.db.migrations.test_pike_expand01 as tpe01
import titicaca.tests.utils as test_utils


# no TestPikeMigrate01Mixin class needed, can use TestPikeExpand01Mixin instead


class TestPikeMigrate01MySQL(
    tpe01.TestPikeExpand01Mixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.MySQLOpportunisticFixture
