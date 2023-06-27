# Copyright 2020 Red Hat, Inc
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.
import titicaca_store
from oslo_config import cfg
from oslo_upgradecheck import upgradecheck

from titicaca.cmd.status import Checks
from titicaca.tests import utils as test_utils

CONF = cfg.CONF


class TestUpgradeChecks(test_utils.BaseTestCase):
    def setUp(self):
        super(TestUpgradeChecks, self).setUp()
        titicaca_store.register_opts(CONF)
        self.checker = Checks()

    def test_sheepdog_removal_no_config(self):
        self.assertEqual(self.checker._check_sheepdog_store().code,
                         upgradecheck.Code.SUCCESS)

    def test_sheepdog_removal_enabled_backends(self):
        self.config(enabled_backends=None)
        self.assertEqual(self.checker._check_sheepdog_store().code,
                         upgradecheck.Code.SUCCESS)

        self.config(enabled_backends={})
        self.assertEqual(self.checker._check_sheepdog_store().code,
                         upgradecheck.Code.SUCCESS)

        self.config(enabled_backends={'foo': 'bar'})
        self.assertEqual(self.checker._check_sheepdog_store().code,
                         upgradecheck.Code.SUCCESS)

        self.config(enabled_backends={'sheepdog': 'foobar'})
        self.assertEqual(self.checker._check_sheepdog_store().code,
                         upgradecheck.Code.FAILURE)

    def test_sheepdog_removal_titicaca_store_stores(self):
        self.config(stores=None, group='titicaca_store')
        self.assertEqual(self.checker._check_sheepdog_store().code,
                         upgradecheck.Code.SUCCESS)

        self.config(stores='', group='titicaca_store')
        self.assertEqual(self.checker._check_sheepdog_store().code,
                         upgradecheck.Code.SUCCESS)

        self.config(stores='foo', group='titicaca_store')
        self.assertEqual(self.checker._check_sheepdog_store().code,
                         upgradecheck.Code.SUCCESS)

        self.config(stores='sheepdog', group='titicaca_store')
        self.assertEqual(self.checker._check_sheepdog_store().code,
                         upgradecheck.Code.FAILURE)

    def test_owner_is_tenant_removal(self):
        self.config(owner_is_tenant=True)
        self.assertEqual(self.checker._check_owner_is_tenant().code,
                         upgradecheck.Code.SUCCESS)

        self.config(owner_is_tenant=False)
        self.assertEqual(self.checker._check_owner_is_tenant().code,
                         upgradecheck.Code.FAILURE)
