# Copyright 2011 Justin Santa Barbara
# Copyright 2012 OpenStack Foundation
# Copyright 2019 Red Hat
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""Implementation of a fake key manager."""


from castellan.tests.unit.key_manager import mock_key_manager


def fake_api(configuration=None):
    return mock_key_manager.MockKeyManager(configuration)
