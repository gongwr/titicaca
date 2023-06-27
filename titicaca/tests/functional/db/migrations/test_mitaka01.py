# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from oslo_db.sqlalchemy import test_fixtures
import sqlalchemy

from titicaca.tests.functional.db import test_migrations
import titicaca.tests.utils as test_utils


def get_indexes(table, engine):
    inspector = sqlalchemy.inspect(engine)
    return [idx['name'] for idx in inspector.get_indexes(table)]


class TestMitaka01Mixin(test_migrations.AlembicMigrationsMixin):

    def _pre_upgrade_mitaka01(self, engine):
        indexes = get_indexes('images', engine)
        self.assertNotIn('created_at_image_idx', indexes)
        self.assertNotIn('updated_at_image_idx', indexes)

    def _check_mitaka01(self, engine, data):
        indexes = get_indexes('images', engine)
        self.assertIn('created_at_image_idx', indexes)
        self.assertIn('updated_at_image_idx', indexes)


class TestMitaka01MySQL(
    TestMitaka01Mixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.MySQLOpportunisticFixture


class TestMitaka01PostgresSQL(
    TestMitaka01Mixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.PostgresqlOpportunisticFixture


class TestMitaka01Sqlite(
    TestMitaka01Mixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    pass
