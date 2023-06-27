# Copyright (C) 2021 RedHat Inc
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""add image_id, request_id, user columns to tasks table"

Revision ID: wallaby_expand01
Revises: ussuri_expand01
Create Date: 2021-02-04 11:55:16.657499

"""

from alembic import op
from sqlalchemy import String, Column

# revision identifiers, used by Alembic.
revision = 'wallaby_expand01'
down_revision = 'ussuri_expand01'
branch_labels = None
depends_on = None


def upgrade():
    image_id_col = Column('image_id', String(length=36), nullable=True)
    request_id_col = Column('request_id', String(length=64), nullable=True)
    user_col = Column('user_id', String(length=64), nullable=True)
    op.add_column('tasks', image_id_col)
    op.add_column('tasks', request_id_col)
    op.add_column('tasks', user_col)
    op.create_index('ix_tasks_image_id', 'tasks', ['image_id'])
