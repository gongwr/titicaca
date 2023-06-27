# Copyright 2013 Rackspace Hosting
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import atexit
import os.path
import shutil
import tempfile

import fixtures
import titicaca_store
from oslo_config import cfg
from oslo_db import options

import titicaca.common.client
from titicaca.common import config
import titicaca.db.sqlalchemy.api
from titicaca import tests as titicaca_tests
from titicaca.tests import utils as test_utils


TESTING_API_PASTE_CONF = """
[pipeline:titicaca-api]
pipeline = versionnegotiation gzip unauthenticated-context rootapp

[pipeline:titicaca-api-caching]
pipeline = versionnegotiation gzip unauthenticated-context cache rootapp

[pipeline:titicaca-api-cachemanagement]
pipeline =
    versionnegotiation
    gzip
    unauthenticated-context
    cache
    cache_manage
    rootapp

[pipeline:titicaca-api-fakeauth]
pipeline = versionnegotiation gzip fakeauth context rootapp

[pipeline:titicaca-api-noauth]
pipeline = versionnegotiation gzip context rootapp

[composite:rootapp]
paste.composite_factory = titicaca.api:root_app_factory
/: apiversions
/v2: apiv2app

[app:apiversions]
paste.app_factory = titicaca.api.versions:create_resource

[app:apiv2app]
paste.app_factory = titicaca.api.v2.router:API.factory

[filter:versionnegotiation]
paste.filter_factory =
 titicaca.api.middleware.version_negotiation:VersionNegotiationFilter.factory

[filter:gzip]
paste.filter_factory = titicaca.api.middleware.gzip:GzipMiddleware.factory

[filter:cache]
paste.filter_factory = titicaca.api.middleware.cache:CacheFilter.factory

[filter:cache_manage]
paste.filter_factory =
 titicaca.api.middleware.cache_manage:CacheManageFilter.factory

[filter:context]
paste.filter_factory = titicaca.api.middleware.context:ContextMiddleware.factory

[filter:unauthenticated-context]
paste.filter_factory =
 titicaca.api.middleware.context:UnauthenticatedContextMiddleware.factory

[filter:fakeauth]
paste.filter_factory = titicaca.tests.utils:FakeAuthMiddleware.factory
"""

CONF = cfg.CONF


class ApiTest(test_utils.BaseTestCase):

    def setUp(self):
        super(ApiTest, self).setUp()
        self.test_dir = self.useFixture(fixtures.TempDir()).path
        self._configure_logging()
        self._setup_database()
        self._setup_stores()
        self._setup_property_protection()
        self.titicaca_api_app = self._load_paste_app(
            'titicaca-api',
            flavor=getattr(self, 'api_flavor', ''),
            conf=getattr(self, 'api_paste_conf', TESTING_API_PASTE_CONF),
        )
        self.http = test_utils.Httplib2WsgiAdapter(self.titicaca_api_app)

    def _setup_property_protection(self):
        self._copy_data_file('property-protections.conf', self.test_dir)
        self.property_file = os.path.join(self.test_dir,
                                          'property-protections.conf')

    def _configure_logging(self):
        self.config(default_log_levels=[
            'amqplib=WARN',
            'sqlalchemy=WARN',
            'boto=WARN',
            'suds=INFO',
            'keystone=INFO',
            'eventlet.wsgi.server=DEBUG'
        ])

    def _setup_database(self):
        sql_connection = 'sqlite:////%s/tests.sqlite' % self.test_dir
        options.set_defaults(CONF, connection=sql_connection)
        titicaca.db.sqlalchemy.api.clear_db_env()
        titicaca_db_env = 'TITICACA_DB_TEST_SQLITE_FILE'
        if titicaca_db_env in os.environ:
            # use the empty db created and cached as a tempfile
            # instead of spending the time creating a new one
            db_location = os.environ[titicaca_db_env]
            shutil.copyfile(db_location, "%s/tests.sqlite" % self.test_dir)
        else:
            test_utils.db_sync()

            # copy the clean db to a temp location so that it
            # can be reused for future tests
            (osf, db_location) = tempfile.mkstemp()
            os.close(osf)
            shutil.copyfile('%s/tests.sqlite' % self.test_dir, db_location)
            os.environ[titicaca_db_env] = db_location

            # cleanup the temp file when the test suite is
            # complete
            def _delete_cached_db():
                try:
                    os.remove(os.environ[titicaca_db_env])
                except Exception:
                    titicaca_tests.logger.exception(
                        "Error cleaning up the file %s" %
                        os.environ[titicaca_db_env])
            atexit.register(_delete_cached_db)

    def _setup_stores(self):
        titicaca_store.register_opts(CONF)

        image_dir = os.path.join(self.test_dir, "images")
        self.config(group='titicaca_store',
                    filesystem_store_datadir=image_dir)

        titicaca_store.create_stores()

    def _load_paste_app(self, name, flavor, conf):
        conf_file_path = os.path.join(self.test_dir, '%s-paste.ini' % name)
        with open(conf_file_path, 'w') as conf_file:
            conf_file.write(conf)
            conf_file.flush()
        return config.load_paste_app(name, flavor=flavor,
                                     conf_file=conf_file_path)

    def tearDown(self):
        titicaca.db.sqlalchemy.api.clear_db_env()
        super(ApiTest, self).tearDown()
