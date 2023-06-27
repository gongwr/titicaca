# Copyright 2021 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.
from oslo_policy import policy


discovery_policies = [
    policy.DocumentedRuleDefault(
        name="stores_info_detail",
        check_str='role:admin',
        scope_types=['system', 'project'],
        description='Expose store specific information',
        operations=[
            {'path': '/v2/info/stores/detail',
             'method': 'GET'}
        ]
    ),
]


def list_rules():
    return discovery_policies
