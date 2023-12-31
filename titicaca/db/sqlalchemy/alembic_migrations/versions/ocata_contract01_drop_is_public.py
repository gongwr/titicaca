# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""remove is_public from images

Revision ID: ocata_contract01
Revises: mitaka02
Create Date: 2017-01-27 12:58:16.647499

"""

from alembic import op
from sqlalchemy import MetaData, Enum

from titicaca.cmd import manage
from titicaca.db import migration

# revision identifiers, used by Alembic.
revision = 'ocata_contract01'
down_revision = 'mitaka02'
branch_labels = ('ocata01', migration.CONTRACT_BRANCH)
depends_on = 'ocata_expand01'


MYSQL_DROP_INSERT_TRIGGER = """
DROP TRIGGER insert_visibility;
"""

MYSQL_DROP_UPDATE_TRIGGER = """
DROP TRIGGER update_visibility;
"""


def _drop_column():
    with op.batch_alter_table('images') as batch_op:
        batch_op.drop_index('ix_images_is_public')
        batch_op.drop_column('is_public')


def _drop_triggers(engine):
    engine_name = engine.engine.name
    if engine_name == "mysql":
        op.execute(MYSQL_DROP_INSERT_TRIGGER)
        op.execute(MYSQL_DROP_UPDATE_TRIGGER)


def _set_nullability_and_default_on_visibility(meta):
    # NOTE(hemanthm): setting the default on 'visibility' column
    # to 'shared'. Also, marking it as non-nullable.
    # images = Table('images', meta, autoload=True)
    existing_type = Enum('private', 'public', 'shared', 'community',
                         metadata=meta, name='image_visibility')
    with op.batch_alter_table('images') as batch_op:
        batch_op.alter_column('visibility',
                              nullable=False,
                              server_default='shared',
                              existing_type=existing_type)


def upgrade():
    migrate_engine = op.get_bind()
    meta = MetaData(bind=migrate_engine)

    _drop_column()
    if manage.USE_TRIGGERS:
        _drop_triggers(migrate_engine)
    _set_nullability_and_default_on_visibility(meta)
