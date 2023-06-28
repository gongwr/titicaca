# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
SQLAlchemy models for titicaca data
"""

from oslo_db.sqlalchemy import models
from oslo_serialization import jsonutils
from sqlalchemy import Boolean, Column, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator

from titicaca.common import timeutils

BASE = declarative_base()


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string"""

    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = jsonutils.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = jsonutils.loads(value)
        return value


class TiticacaBase(models.ModelBase, models.TimestampMixin):
    """Base class for Titicaca Models."""

    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    __table_initialized__ = False
    __protected_attributes__ = {"created_at", "updated_at", "deleted_at", "deleted"}

    def save(self, session=None):
        from titicaca.db.sqlalchemy import api as db_api
        super(TiticacaBase, self).save(session or db_api.get_session())

    created_at = Column(DateTime, default=lambda: timeutils.utcnow(),
                        nullable=False)
    # TODO(vsergeyev): Column `updated_at` have no default value in
    #                  OpenStack common code. We should decide, is this value
    #                  required and make changes in oslo (if required) or
    #                  in titicaca (if not).
    updated_at = Column(DateTime, default=lambda: timeutils.utcnow(),
                        nullable=True, onupdate=lambda: timeutils.utcnow())
    # TODO(boris-42): Use SoftDeleteMixin instead of deleted Column after
    #                 migration that provides UniqueConstraints and change
    #                 type of this column.
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, nullable=False, default=False)

    def delete(self, session=None):
        """Delete this object."""
        self.deleted = True
        self.deleted_at = timeutils.utcnow()
        self.save(session=session)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def to_dict(self):
        d = self.__dict__.copy()
        # NOTE(flaper87): Remove
        # private state instance
        # It is not serializable
        # and causes CircularReference
        d.pop("_sa_instance_state")
        return d
