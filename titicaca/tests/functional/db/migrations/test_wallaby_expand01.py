#    Copyright (c) 2021 RedHat, Inc.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from oslo_db.sqlalchemy import test_fixtures
from oslo_db.sqlalchemy import utils as db_utils

from titicaca.tests.functional.db import test_migrations
import titicaca.tests.utils as test_utils


class TestWallabyExpand01Mixin(test_migrations.AlembicMigrationsMixin):

    def _get_revisions(self, config):
        return test_migrations.AlembicMigrationsMixin._get_revisions(
            self, config, head='wallaby_expand01')

    def _pre_upgrade_wallaby_expand01(self, engine):
        tasks = db_utils.get_table(engine, 'tasks')
        self.assertNotIn('image_id', tasks.c)
        self.assertNotIn('request_id', tasks.c)
        self.assertNotIn('user_id', tasks.c)
        self.assertFalse(db_utils.index_exists(engine, 'tasks',
                                               'ix_tasks_image_id'))

    def _check_wallaby_expand01(self, engine, data):
        # check that after migration, 'image_id', 'request_id', 'user'
        # columns are added
        tasks = db_utils.get_table(engine, 'tasks')
        self.assertIn('image_id', tasks.c)
        self.assertIn('request_id', tasks.c)
        self.assertIn('user_id', tasks.c)
        self.assertTrue(tasks.c.image_id.nullable)
        self.assertTrue(tasks.c.request_id.nullable)
        self.assertTrue(tasks.c.user_id.nullable)
        self.assertTrue(db_utils.index_exists(engine, 'tasks',
                                              'ix_tasks_image_id'),
                        'Index %s on table %s does not exist' %
                        ('ix_tasks_image_id', 'tasks'))


class TestWallabyExpand01MySQL(
    TestWallabyExpand01Mixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.MySQLOpportunisticFixture
