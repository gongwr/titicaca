# Copyright (C) 2018 Verizon Wireless
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""add os_hash_algo and os_hash_value columns to images table"""

from alembic import op
from sqlalchemy import Column, String

# revision identifiers, used by Alembic.
revision = 'rocky_expand02'
down_revision = 'rocky_expand01'
branch_labels = None
depends_on = None


def upgrade():
    algo_col = Column('os_hash_algo', String(length=64), nullable=True)
    value_col = Column('os_hash_value', String(length=128), nullable=True)
    op.add_column('images', algo_col)
    op.add_column('images', value_col)
    op.create_index('os_hash_value_image_idx', 'images', ['os_hash_value'])
