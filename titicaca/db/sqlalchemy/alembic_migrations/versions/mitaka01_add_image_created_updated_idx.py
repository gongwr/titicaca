# Copyright 2016 Rackspace
# Copyright 2013 Intel Corporation
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""add index on created_at and updated_at columns of 'images' table

Revision ID: mitaka01
Revises: liberty
Create Date: 2016-08-03 17:19:35.306161

"""

from alembic import op
from sqlalchemy import MetaData, Table, Index


# revision identifiers, used by Alembic.
revision = 'mitaka01'
down_revision = 'liberty'
branch_labels = None
depends_on = None

CREATED_AT_INDEX = 'created_at_image_idx'
UPDATED_AT_INDEX = 'updated_at_image_idx'


def upgrade():
    migrate_engine = op.get_bind()
    meta = MetaData(bind=migrate_engine)

    images = Table('images', meta, autoload=True)

    created_index = Index(CREATED_AT_INDEX, images.c.created_at)
    created_index.create(migrate_engine)
    updated_index = Index(UPDATED_AT_INDEX, images.c.updated_at)
    updated_index.create(migrate_engine)
