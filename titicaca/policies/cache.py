# Copyright (c) 2023 WenRui Gong
# All rights reserved.
from oslo_log import versionutils
from oslo_policy import policy

from titicaca.policies import base


DEPRECATED_REASON = """
The image API now supports roles.
"""


cache_policies = [
    policy.DocumentedRuleDefault(
        name="cache_image",
        check_str=base.ADMIN,
        scope_types=['project'],
        description='Queue image for caching',
        operations=[
            {'path': '/v2/cache/{image_id}',
             'method': 'PUT'}
        ],
        deprecated_rule=policy.DeprecatedRule(
            name="cache_image", check_str="rule:manage_image_cache",
            deprecated_reason=DEPRECATED_REASON,
            deprecated_since=versionutils.deprecated.XENA
        ),
    ),
    policy.DocumentedRuleDefault(
        name="cache_list",
        check_str=base.ADMIN,
        scope_types=['project'],
        description='List cache status',
        operations=[
            {'path': '/v2/cache',
             'method': 'GET'}
        ],
        deprecated_rule=policy.DeprecatedRule(
            name="cache_list", check_str="rule:manage_image_cache",
            deprecated_reason=DEPRECATED_REASON,
            deprecated_since=versionutils.deprecated.XENA
        ),
    ),
    policy.DocumentedRuleDefault(
        name="cache_delete",
        check_str=base.ADMIN,
        scope_types=['project'],
        description='Delete image(s) from cache and/or queue',
        operations=[
            {'path': '/v2/cache',
             'method': 'DELETE'},
            {'path': '/v2/cache/{image_id}',
             'method': 'DELETE'}
        ],
        deprecated_rule=policy.DeprecatedRule(
            name="cache_delete", check_str="rule:manage_image_cache",
            deprecated_reason=DEPRECATED_REASON,
            deprecated_since=versionutils.deprecated.XENA
        ),
    ),
]


def list_rules():
    return cache_policies
