#    Copyright (c) 2018 RedHat, Inc.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from oslo_db.sqlalchemy import test_fixtures
from oslo_db.sqlalchemy import utils as db_utils

from titicaca.tests.functional.db import test_migrations
import titicaca.tests.utils as test_utils


class TestRockyExpand01Mixin(test_migrations.AlembicMigrationsMixin):

    def _get_revisions(self, config):
        return test_migrations.AlembicMigrationsMixin._get_revisions(
            self, config, head='rocky_expand01')

    def _pre_upgrade_rocky_expand01(self, engine):
        images = db_utils.get_table(engine, 'images')
        self.assertNotIn('os_hidden', images.c)

    def _check_rocky_expand01(self, engine, data):
        # check that after migration, 'os_hidden' column is introduced
        images = db_utils.get_table(engine, 'images')
        self.assertIn('os_hidden', images.c)
        self.assertFalse(images.c.os_hidden.nullable)


class TestRockyExpand01MySQL(
    TestRockyExpand01Mixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.MySQLOpportunisticFixture
