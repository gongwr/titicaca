# Copyright (c) 2023 WenRui Gong
# All rights reserved.



from alembic import op
from sqlalchemy import MetaData, Enum

from titicaca.cmd import manage
from titicaca.db import migration

# revision identifiers, used by Alembic.
revision = 'bravo_contract01'
down_revision = 'alpha'
branch_labels = ('bravo01', migration.CONTRACT_BRANCH)
depends_on = 'bravo_expand01'


def upgrade():
    pass