# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
Various conveniences used for migration scripts
"""

from oslo_log import log as logging
import sqlalchemy.types


LOG = logging.getLogger(__name__)


def String(length):
    return sqlalchemy.types.String(
        length=length, convert_unicode=False,
        unicode_error=None, _warn_on_bytestring=False)


def Text():
    return sqlalchemy.types.Text(
        length=None, convert_unicode=False,
        unicode_error=None, _warn_on_bytestring=False)


def Boolean():
    return sqlalchemy.types.Boolean(create_constraint=True, name=None)


def DateTime():
    return sqlalchemy.types.DateTime(timezone=False)


def Integer():
    return sqlalchemy.types.Integer()


def BigInteger():
    return sqlalchemy.types.BigInteger()


def PickleType():
    return sqlalchemy.types.PickleType()


def Numeric():
    return sqlalchemy.types.Numeric()
