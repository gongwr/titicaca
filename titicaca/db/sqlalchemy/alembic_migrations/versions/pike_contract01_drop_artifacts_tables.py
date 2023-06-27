# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""drop glare artifacts tables

Revision ID: pike_contract01
Revises: ocata_contract01
Create Date: 2017-02-09 20:32:51.222867

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'pike_contract01'
down_revision = 'ocata_contract01'
branch_labels = None
depends_on = 'pike_expand01'


def upgrade():
    # create list of artifact tables in reverse order of their creation
    table_names = []
    table_names.append('artifact_blob_locations')
    table_names.append('artifact_properties')
    table_names.append('artifact_blobs')
    table_names.append('artifact_dependencies')
    table_names.append('artifact_tags')
    table_names.append('artifacts')

    for table_name in table_names:
        op.drop_table(table_name=table_name)
