# Copyright (C) 2018 RedHat Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""add os_hidden column to images table"""

from alembic import op
from sqlalchemy import Boolean, Column, sql

# revision identifiers, used by Alembic.
revision = 'rocky_expand01'
down_revision = 'queens_expand01'
branch_labels = None
depends_on = None


def upgrade():
    h_col = Column('os_hidden', Boolean, default=False, nullable=False,
                   server_default=sql.expression.false())
    op.add_column('images', h_col)
    op.create_index('os_hidden_image_idx', 'images', ['os_hidden'])
