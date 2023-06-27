# Copyright 2011-2014 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import copy

from keystoneauth1 import session
from keystoneauth1 import token_endpoint
from oslo_config import cfg
from oslo_context import context

from titicaca.api import policy

CONF = cfg.CONF


def get_ksa_client(context):
    """Returns a keystoneauth Adapter using token from context.

    This will return a simple keystoneauth adapter that can be used to
    make requests against a remote service using the token provided
    (and already authenticated) from the user and stored in a
    RequestContext.

    :param context: User request context
    :returns: keystoneauth1 Adapter object
    """
    auth = token_endpoint.Token(CONF.keystone_authtoken.identity_uri,
                                context.auth_token)
    return session.Session(auth=auth)


class RequestContext(context.RequestContext):
    """Stores information about the security context.

    Stores how the user accesses the system, as well as additional request
    information.

    """

    def __init__(self, service_catalog=None, policy_enforcer=None, **kwargs):
        # TODO(mriedem): Remove usage of user and tenant from old tests.
        if 'tenant' in kwargs:
            # Prefer project_id if passed, otherwise alias tenant as project_id
            tenant = kwargs.pop('tenant')
            kwargs['project_id'] = kwargs.get('project_id', tenant)
        if 'user' in kwargs:
            # Prefer user_id if passed, otherwise alias user as user_id
            user = kwargs.pop('user')
            kwargs['user_id'] = kwargs.get('user_id', user)
        super(RequestContext, self).__init__(**kwargs)
        self.service_catalog = service_catalog
        self.policy_enforcer = policy_enforcer or policy.Enforcer()
        if not self.is_admin:
            self.is_admin = self.policy_enforcer.check_is_admin(self)

    def to_dict(self):
        d = super(RequestContext, self).to_dict()
        d.update({
            'roles': self.roles,
            'service_catalog': self.service_catalog,
        })
        return d

    @classmethod
    def from_dict(cls, values):
        return cls(**values)

    @property
    def owner(self):
        """Return the owner to correlate with an image."""
        return self.project_id

    @property
    def can_see_deleted(self):
        """Admins can see deleted by default"""
        return self.show_deleted or self.is_admin

    def elevated(self):
        """Return a copy of this context with admin flag set."""

        context = copy.copy(self)
        context.roles = copy.deepcopy(self.roles)
        if 'admin' not in context.roles:
            context.roles.append('admin')

        context.is_admin = True

        return context


def get_admin_context(show_deleted=False):
    """Create an administrator context."""
    return RequestContext(auth_token=None,
                          project_id=None,
                          is_admin=True,
                          show_deleted=show_deleted,
                          overwrite=False)
