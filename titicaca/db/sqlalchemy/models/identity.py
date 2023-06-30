# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import datetime

from oslo_config import cfg
from oslo_log import log
from sqlalchemy import Boolean, DateTime, Date, Integer, String, Text
from sqlalchemy import Column
from sqlalchemy import ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import collections, relationship

from titicaca.common import password_hashing
from titicaca.common import resource_options
from titicaca.common.resource_options import user_resource_options as uro
from titicaca.db.sqlalchemy.models.base import BASE
from titicaca.db.sqlalchemy.models.base import JSONEncodedDict, DateTimeInt
from titicaca.db.sqlalchemy.models.base import ModelDictMixin, ModelDictMixinWithExtras

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class User(BASE, ModelDictMixinWithExtras):
    __tablename__ = 'user'
    attributes = ['id', 'name', 'domain_id', 'password', 'enabled',
                  'default_project_id', 'password_expires_at']
    readonly_attributes = ['id', 'password_expires_at', 'password']
    resource_options_registry = uro.USER_OPTIONS_REGISTRY
    id = Column(String(64), primary_key=True)
    domain_id = Column(String(64), nullable=False)
    _enabled = Column('enabled', Boolean)
    extra = Column(JSONEncodedDict(), default={})
    default_project_id = Column(String(64), index=True)
    _resource_option_mapper = relationship(
        'UserOption',
        single_parent=True,
        cascade='all,delete,delete-orphan',
        lazy='subquery',
        backref='user',
        collection_class=collections.attribute_keyed_dict('option_id'))
    local_user = relationship('LocalUser', uselist=False,
                              single_parent=True, lazy='joined',
                              cascade='all,delete-orphan', backref='user')
    federated_users = relationship('FederatedUser',
                                   single_parent=True,
                                   lazy='joined',
                                   cascade='all,delete-orphan',
                                   backref='user')
    nonlocal_user = relationship('NonLocalUser',
                                 uselist=False,
                                 single_parent=True,
                                 lazy='joined',
                                 cascade='all,delete-orphan',
                                 backref='user')
    expiring_user_group_memberships = relationship(
        'ExpiringUserGroupMembership',
        cascade='all, delete-orphan',
        backref="user"
    )
    created_at = Column(DateTime, nullable=True)
    last_active_at = Column(Date, nullable=True)
    # unique constraint needed here to support composite fk constraints
    __table_args__ = (UniqueConstraint('id', 'domain_id'), {})

    # NOTE(stevemar): we use a hybrid property here because we leverage the
    # expression method, see `@name.expression` and `LocalUser.name` below.
    @hybrid_property
    def name(self):
        """Return the current username."""
        if self.local_user:
            return self.local_user.name
        elif self.nonlocal_user:
            return self.nonlocal_user.name
        elif self.federated_users:
            return self.federated_users[0].display_name
        else:
            return None

    @name.setter
    def name(self, value):
        if self.federated_users:
            self.federated_users[0].display_name = value
        elif self.local_user:
            self.local_user.name = value
        else:
            self.local_user = LocalUser()
            self.local_user.name = value

    @name.expression
    def name(self):
        return LocalUser.name

    # password properties
    @property
    def password_ref(self):
        """Return the current password ref."""
        if self.local_user and self.local_user.passwords:
            return self.local_user.passwords[-1]
        return None

    # NOTE(stevemar): we use a hybrid property here because we leverage the
    # expression method, see `@password.expression` and `Password.password`
    # below.
    @hybrid_property
    def password(self):
        """Return the current password."""
        if self.password_ref:
            return self.password_ref.password_hash
        return None

    @property
    def password_created_at(self):
        """Return when password was created at."""
        if self.password_ref:
            return self.password_ref.created_at
        return None

    @property
    def password_expires_at(self):
        """Return when password expires at."""
        if self.password_ref:
            return self.password_ref.expires_at
        return None

    @property
    def password_is_expired(self):
        """Return whether password is expired or not."""
        if self.password_expires_at and not self._password_expiry_exempt():
            return datetime.datetime.utcnow() >= self.password_expires_at
        return False

    @password.setter
    def password(self, value):
        now = datetime.datetime.utcnow()
        if not self.local_user:
            self.local_user = LocalUser()
        # truncate extra passwords
        if self.local_user.passwords:
            unique_cnt = CONF.security_compliance.unique_last_password_count
            unique_cnt = unique_cnt + 1 if unique_cnt == 0 else unique_cnt
            self.local_user.passwords = self.local_user.passwords[-unique_cnt:]
        # set all previous passwords to be expired
        for ref in self.local_user.passwords:
            if not ref.expires_at or ref.expires_at > now:
                ref.expires_at = now
        new_password_ref = Password()

        hashed_passwd = None
        if value is not None:
            # NOTE(notmorgan): hash the passwords, never directly bind the
            # "value" in the unhashed form to hashed_passwd to ensure the
            # unhashed password cannot end up in the db. If an unhashed
            # password ends up in the DB, it cannot be used for auth, it is
            # however incorrect and could leak user credentials (due to users
            # doing insecure things such as sharing passwords across
            # different systems) to unauthorized parties.
            hashed_passwd = password_hashing.hash_password(value)

        new_password_ref.password_hash = hashed_passwd
        new_password_ref.created_at = now
        new_password_ref.expires_at = self._get_password_expires_at(now)
        self.local_user.passwords.append(new_password_ref)

    def _password_expiry_exempt(self):
        # Get the IGNORE_PASSWORD_EXPIRY_OPT value from the user's
        # option_mapper.
        return getattr(
            self.get_resource_option(uro.IGNORE_PASSWORD_EXPIRY_OPT.option_id),
            'option_value',
            False)

    def _get_password_expires_at(self, created_at):
        expires_days = CONF.security_compliance.password_expires_days
        if not self._password_expiry_exempt():
            if expires_days:
                expired_date = (created_at +
                                datetime.timedelta(days=expires_days))
                return expired_date.replace(microsecond=0)
        return None

    @password.expression
    def password(self):
        return Password.password_hash

    # NOTE(stevemar): we use a hybrid property here because we leverage the
    # expression method, see `@enabled.expression` and `User._enabled` below.
    @hybrid_property
    def enabled(self):
        """Return whether user is enabled or not."""
        if self._enabled:
            max_days = (
                CONF.security_compliance.disable_user_account_days_inactive)
            inactivity_exempt = getattr(
                self.get_resource_option(uro.IGNORE_USER_INACTIVITY_OPT.option_id),
                'option_value',
                False)
            last_active = self.last_active_at
            if not last_active and self.created_at:
                last_active = self.created_at.date()
            if max_days and last_active:
                now = datetime.datetime.utcnow().date()
                days_inactive = (now - last_active).days
                if days_inactive >= max_days and not inactivity_exempt:
                    self._enabled = False
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if (value and
                CONF.security_compliance.disable_user_account_days_inactive):
            self.last_active_at = datetime.datetime.utcnow().date()
        if value and self.local_user:
            self.local_user.failed_auth_count = 0
            self.local_user.failed_auth_at = None
        self._enabled = value

    @enabled.expression
    def enabled(self):
        return User._enabled

    def get_resource_option(self, option_id):
        if option_id in self._resource_option_mapper.keys():
            return self._resource_option_mapper[option_id]
        return None

    def to_dict(self, include_extra_dict=False):
        d = super(User, self).to_dict(include_extra_dict=include_extra_dict)
        if 'default_project_id' in d and d['default_project_id'] is None:
            del d['default_project_id']
        # NOTE(notmorgan): Eventually it may make sense to drop the empty
        # option dict creation to the superclass (if enough models use it)
        d['options'] = resource_options.ref_mapper_to_dict_options(self)
        return d

    @classmethod
    def from_dict(cls, user_dict):
        """Override from_dict to remove password_expires_at attribute.

        Overriding this method to remove password_expires_at attribute to
        support update_user and unit tests where password_expires_at
        inadvertently gets added by calling to_dict followed by from_dict.

        :param user_dict: User entity dictionary
        :returns User: User object

        """
        new_dict = user_dict.copy()
        new_resource_options = {}
        options = new_dict.pop('options', {})
        password_expires_at_key = 'password_expires_at'  # nosec
        if password_expires_at_key in user_dict:
            del new_dict[password_expires_at_key]
        for opt in cls.resource_options_registry.options:
            if opt.option_name in options:
                opt_value = options[opt.option_name]
                # NOTE(notmorgan): None is always a valid type
                if opt_value is not None:
                    opt.validator(opt_value)
                new_resource_options[opt.option_id] = opt_value
        user_obj = super(User, cls).from_dict(new_dict)
        setattr(user_obj, '_resource_options', new_resource_options)
        return user_obj


class LocalUser(BASE, ModelDictMixin):
    __tablename__ = 'local_user'
    attributes = ['id', 'user_id', 'domain_id', 'name']
    id = Column(Integer, primary_key=True)
    user_id = Column(String(64))
    domain_id = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    passwords = relationship('Password',
                             single_parent=True,
                             cascade='all,delete-orphan',
                             lazy='joined',
                             backref='local_user',
                             order_by='Password.created_at_int')
    failed_auth_count = Column(Integer, nullable=True)
    failed_auth_at = Column(DateTime, nullable=True)
    __table_args__ = (
        UniqueConstraint('user_id'),
        UniqueConstraint('domain_id', 'name'),
        ForeignKeyConstraint(['user_id', 'domain_id'],
                             ['user.id', 'user.domain_id'],
                             onupdate='CASCADE', ondelete='CASCADE')
    )


class Password(BASE, ModelDictMixin):
    __tablename__ = 'password'
    attributes = ['id', 'local_user_id', 'password_hash', 'created_at',
                  'expires_at']
    id = Column(Integer, primary_key=True)
    local_user_id = Column(Integer, ForeignKey('local_user.id',
                                               ondelete='CASCADE'))
    password_hash = Column(String(255), nullable=True)

    # TODO(lbragstad): Once Rocky opens for development, the _created_at and
    # _expires_at attributes/columns can be removed from the schema. The
    # migration ensures all passwords are converted from datetime objects to
    # big integers. The old datetime columns and their corresponding attributes
    # in the model are no longer required.
    # created_at default set here to safe guard in case it gets missed
    _created_at = Column('created_at', DateTime, nullable=False,
                         default=datetime.datetime.utcnow)
    _expires_at = Column('expires_at', DateTime, nullable=True)
    # set the default to 0, a 0 indicates it is unset.
    created_at_int = Column(DateTimeInt(), nullable=False,
                            default=datetime.datetime.utcnow)
    expires_at_int = Column(DateTimeInt(), nullable=True)
    self_service = Column(Boolean, default=False, nullable=False,
                          server_default='0')

    @hybrid_property
    def created_at(self):
        return self.created_at_int or self._created_at

    @created_at.setter
    def created_at(self, value):
        self._created_at = value
        self.created_at_int = value

    @hybrid_property
    def expires_at(self):
        return self.expires_at_int or self._expires_at

    @expires_at.setter
    def expires_at(self, value):
        self._expires_at = value
        self.expires_at_int = value


class FederatedUser(BASE, ModelDictMixin):
    __tablename__ = 'federated_user'
    attributes = ['id', 'user_id', 'idp_id', 'protocol_id', 'unique_id',
                  'display_name']
    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), ForeignKey('user.id',
                                            ondelete='CASCADE'))
    idp_id = Column(String(64), ForeignKey('identity_provider.id',
                                           ondelete='CASCADE'))
    protocol_id = Column(String(64), nullable=False)
    unique_id = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    __table_args__ = (
        UniqueConstraint('idp_id', 'protocol_id', 'unique_id'),
        ForeignKeyConstraint(['protocol_id', 'idp_id'],
                             ['federation_protocol.id',
                              'federation_protocol.idp_id'],
                             ondelete='CASCADE')
    )


class NonLocalUser(BASE, ModelDictMixin):
    """SQL data model for nonlocal users (LDAP and custom)."""

    __tablename__ = 'nonlocal_user'
    attributes = ['domain_id', 'name', 'user_id']
    domain_id = Column(String(64), primary_key=True)
    name = Column(String(255), primary_key=True)
    user_id = Column(String(64))
    __table_args__ = (
        UniqueConstraint('user_id'),
        ForeignKeyConstraint(
            ['user_id', 'domain_id'], ['user.id', 'user.domain_id'],
            onupdate='CASCADE', ondelete='CASCADE'),)


class Group(BASE, ModelDictMixinWithExtras):
    __tablename__ = 'group'
    attributes = ['id', 'name', 'domain_id', 'description']
    id = Column(String(64), primary_key=True)
    name = Column(String(64), nullable=False)
    domain_id = Column(String(64), nullable=False)
    description = Column(Text())
    extra = Column(JSONEncodedDict(), default={})
    expiring_user_group_memberships = relationship(
        'ExpiringUserGroupMembership',
        cascade='all, delete-orphan',
        backref="group"
    )
    # Unique constraint across two columns to create the separation
    # rather than just only 'name' being unique
    __table_args__ = (UniqueConstraint('domain_id', 'name'),)


class UserGroupMembership(BASE, ModelDictMixin):
    """Group membership join table."""

    __tablename__ = 'user_group_membership'
    user_id = Column(String(64),
                     ForeignKey('user.id'),
                     primary_key=True)
    group_id = Column(String(64),
                      ForeignKey('group.id'),
                      primary_key=True)


class ExpiringUserGroupMembership(BASE, ModelDictMixin):
    """Expiring group membership through federation mapping rules."""

    __tablename__ = 'expiring_user_group_membership'
    user_id = Column(String(64),
                     ForeignKey('user.id'),
                     primary_key=True)
    group_id = Column(String(64),
                      ForeignKey('group.id'),
                      primary_key=True)
    idp_id = Column(String(64),
                    ForeignKey('identity_provider.id',
                               ondelete='CASCADE'),
                    primary_key=True)
    last_verified = Column(DateTime, nullable=False)

    @hybrid_property
    def expires(self):
        ttl = self.idp.authorization_ttl
        if not ttl:
            ttl = CONF.federation.default_authorization_ttl
        return self.last_verified + datetime.timedelta(minutes=ttl)

    @hybrid_property
    def expired(self):
        return self.expires <= datetime.datetime.utcnow()


class UserOption(BASE):
    __tablename__ = 'user_option'
    user_id = Column(String(64), ForeignKey('user.id',
                                            ondelete='CASCADE'), nullable=False,
                     primary_key=True)
    option_id = Column(String(4), nullable=False,
                       primary_key=True)
    option_value = Column(JSONEncodedDict(), default={}, nullable=True)

    def __init__(self, option_id, option_value):
        self.option_id = option_id
        self.option_value = option_value
