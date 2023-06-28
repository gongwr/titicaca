# Copyright 2016 Rackspace
# Copyright 2013 Intel Corporation
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""update metadef os_amazon_server

Revision ID: mitaka02
Revises: mitaka01
Create Date: 2016-08-03 17:23:23.041663

"""

from alembic import op
from sqlalchemy import MetaData, Table


# revision identifiers, used by Alembic.
revision = 'mitaka02'
down_revision = 'mitaka01'
branch_labels = None
depends_on = None


def upgrade():
    migrate_engine = op.get_bind()
    meta = MetaData()

    resource_types_table = Table('metadef_resource_types', meta, autoload_with=migrate_engine)

    resource_types_table.update(values={'name': 'OS::Amazon::Server'}).where(
        resource_types_table.c.name == 'OS::Amazon::Instance').execute()
