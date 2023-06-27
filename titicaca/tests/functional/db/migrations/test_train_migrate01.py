# Copyright 2019 RedHat Inc
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import datetime

from oslo_db.sqlalchemy import test_fixtures
from oslo_db.sqlalchemy import utils as db_utils

from titicaca.db.sqlalchemy.alembic_migrations import data_migrations
from titicaca.tests.functional.db import test_migrations
import titicaca.tests.utils as test_utils


class TestTrainMigrate01Mixin(test_migrations.AlembicMigrationsMixin):

    def _get_revisions(self, config):
        return test_migrations.AlembicMigrationsMixin._get_revisions(
            self, config, head='train_expand01')

    def _pre_upgrade_train_expand01(self, engine):
        images = db_utils.get_table(engine, 'images')
        image_locations = db_utils.get_table(engine, 'image_locations')
        now = datetime.datetime.now()

        # inserting a public image record
        image_1 = dict(deleted=False,
                       created_at=now,
                       status='active',
                       min_disk=0,
                       min_ram=0,
                       visibility='public',
                       id='image_1')
        with engine.connect() as conn, conn.begin():
            conn.execute(images.insert().values(image_1))

        image_2 = dict(deleted=False,
                       created_at=now,
                       status='active',
                       min_disk=0,
                       min_ram=0,
                       visibility='public',
                       id='image_2')
        with engine.connect() as conn, conn.begin():
            conn.execute(images.insert().values(image_2))

        # adding records to image_locations tables
        temp = dict(deleted=False,
                    created_at=now,
                    image_id='image_1',
                    value='image_location_1',
                    meta_data='{"backend": "fast"}',
                    id=1)
        with engine.connect() as conn, conn.begin():
            conn.execute(image_locations.insert().values(temp))

        temp = dict(deleted=False,
                    created_at=now,
                    image_id='image_2',
                    value='image_location_2',
                    meta_data='{"backend": "cheap"}',
                    id=2)
        with engine.connect() as conn, conn.begin():
            conn.execute(image_locations.insert().values(temp))

    def _check_train_expand01(self, engine, data):
        image_locations = db_utils.get_table(engine, 'image_locations')

        # check that meta_data has 'backend' key for existing image_locations
        with engine.connect() as conn:
            rows = conn.execute(
                image_locations.select().order_by(image_locations.c.id)
            ).fetchall()

        self.assertEqual(2, len(rows))
        for row in rows:
            self.assertIn('"backend":', row['meta_data'])

        # run data migrations
        data_migrations.migrate(engine, release='train')

        # check that meta_data has 'backend' key replaced with 'store'
        with engine.connect() as conn:
            rows = conn.execute(
                image_locations.select().order_by(image_locations.c.id)
            ).fetchall()

        self.assertEqual(2, len(rows))
        for row in rows:
            self.assertNotIn('"backend":', row['meta_data'])
            self.assertIn('"store":', row['meta_data'])


class TestTrainMigrate01MySQL(
    TestTrainMigrate01Mixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.MySQLOpportunisticFixture


class TestTrain01PostgresSQL(
    TestTrainMigrate01Mixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.PostgresqlOpportunisticFixture


class TestTrainMigrate01_EmptyDBMixin(test_migrations.AlembicMigrationsMixin):
    """This mixin is used to create an initial titicaca database and upgrade it
    up to the train_expand01 revision.
    """
    def _get_revisions(self, config):
        return test_migrations.AlembicMigrationsMixin._get_revisions(
            self, config, head='train_expand01')

    def _pre_upgrade_train_expand01(self, engine):
        # New/empty database
        pass

    def _check_train_expand01(self, engine, data):
        images = db_utils.get_table(engine, 'images')

        # check that there are no rows in the images table
        with engine.connect() as conn:
            rows = conn.execute(
                images.select().order_by(images.c.id)
            ).fetchall()

        self.assertEqual(0, len(rows))

        # run data migrations
        data_migrations.migrate(engine)


class TestTrainMigrate01_EmptyDBMySQL(
    TestTrainMigrate01_EmptyDBMixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.MySQLOpportunisticFixture


class TestTrainMigrate01_PySQL(
    TestTrainMigrate01_EmptyDBMixin,
    test_fixtures.OpportunisticDBTestMixin,
    test_utils.BaseTestCase,
):
    FIXTURE = test_fixtures.PostgresqlOpportunisticFixture
