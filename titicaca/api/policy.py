# Copyright (c) 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""Policy Engine For Titicaca"""

from oslo_config import cfg
from oslo_log import log as logging
from oslo_policy import opts
from oslo_policy import policy

from titicaca import policies
from titicaca.common import exception

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
_ENFORCER = None

# TODO(gmann): Remove overriding the default value of config options
# 'policy_file', 'enforce_scope', and 'enforce_new_defaults' once
# oslo_policy change their default value to what is overridden here.
DEFAULT_POLICY_FILE = 'policy.yaml'
opts.set_defaults(
    cfg.CONF,
    DEFAULT_POLICY_FILE,
    enforce_scope=True,
    enforce_new_defaults=True)


class Enforcer(policy.Enforcer):
    """Responsible for loading and enforcing rules"""

    def __init__(self, suppress_deprecation_warnings=False):
        """Init a policy Enforcer.
           :param suppress_deprecation_warnings: Whether to suppress the
                                                 deprecation warnings.
        """
        super(Enforcer, self).__init__(CONF, use_conf=True, overwrite=False)
        # NOTE(gmann): Explicitly disable the warnings for policies
        # changing their default check_str. For new RBAC, all the policy
        # defaults have been changed and warning for each policy started
        # filling the logs limit for various tool.
        # Once we move to new defaults only world then we can enable these
        # warning again.
        self.suppress_default_change_warnings = True
        if suppress_deprecation_warnings:
            self.suppress_deprecation_warnings = True
        self.register_defaults(policies.list_rules())

    def add_rules(self, rules):
        """Add new rules to the Rules object"""
        self.set_rules(rules, overwrite=False, use_conf=self.use_conf)

    def enforce(self, context, action, target, registered=True):
        """Verifies that the action is valid on the target in this context.

           :param context: Titicaca request context
           :param action: String representing the action to be checked
           :param target: Dictionary representing the object of the action.
           :raises: `titicaca.common.exception.Forbidden`
           :returns: A non-False value if access is allowed.
        """
        if registered and action not in self.registered_rules:
            raise policy.PolicyNotRegistered(action)
        try:
            return super(Enforcer, self).enforce(action, target,
                                                 context,
                                                 do_raise=True,
                                                 exc=exception.Forbidden,
                                                 action=action)
        except policy.InvalidScope:
            raise exception.Forbidden(action=action)

    def check(self, context, action, target, registered=True):
        """Verifies that the action is valid on the target in this context.

           :param context: Titicaca request context
           :param action: String representing the action to be checked
           :param target: Dictionary representing the object of the action.
           :returns: A non-False value if access is allowed.
        """
        if registered and action not in self.registered_rules:
            raise policy.PolicyNotRegistered(action)
        return super(Enforcer, self).enforce(action,
                                             target,
                                             context)

    def check_is_admin(self, context):
        """Check if the given context is associated with an admin role,
           as defined via the 'context_is_admin' RBAC rule.

           :param context: Titicaca request context
           :returns: A non-False value if context role is admin.
        """
        return self.check(context, 'context_is_admin', context.to_dict())


def get_enforcer():
    CONF([], project='titicaca')
    global _ENFORCER
    if _ENFORCER is None:
        _ENFORCER = Enforcer()
    return _ENFORCER
