# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from oslo_db.sqlalchemy import test_fixtures
from oslo_db.sqlalchemy import utils as db_utils

from titicaca.tests.functional.db import test_migrations
import titicaca.tests.utils as test_utils


class TestPikeExpand01Mixin(test_migrations.AlembicMigrationsMixin):

    artifacts_table_names = [
        'artifact_blob_locations',
        'artifact_properties',
        'artifact_blobs',
        'artifact_dependencies',
        'artifact_tags',
        'artifacts'
    ]

    def _get_revisions(self, config):
        return test_migrations.AlembicMigrationsMixin._get_revisions(
            self, config, head='pike_expand01')

    def _pre_upgrade_pike_expand01(self, engine):
        # verify presence of the artifacts tables
        for table_name in self.artifacts_table_names:
            table = db_utils.get_table(engine, table_name)
            self.assertIsNotNone(table)

    def _check_pike_expand01(self, engine, data):
        # should be no changes, so re-run pre-upgrade check
        self._pre_upgrade_pike_expand01(engine)


class TestPikeExpand01MySQL(
    TestPikeExpand01Mixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.MySQLOpportunisticFixture
