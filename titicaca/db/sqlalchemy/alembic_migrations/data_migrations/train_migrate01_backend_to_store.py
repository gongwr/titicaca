# Copyright 2019 RedHat Inc
# Copyright (c) 2023 WenRui Gong
# All rights reserved.


def has_migrations(engine):
    """Returns true if at least one data row can be migrated.

    There are rows left to migrate if meta_data column has
    {"backend": "...."}

    Note: This method can return a false positive if data migrations
    are running in the background as it's being called.
    """
    sql_query = ("select meta_data from image_locations where "
                 "INSTR(meta_data, '\"backend\":') > 0")

    # NOTE(abhishekk): INSTR function doesn't supported in postgresql
    if engine.name == 'postgresql':
        sql_query = ("select meta_data from image_locations where "
                     "POSITION('\"backend\":' IN meta_data) > 0")

    with engine.connect() as con:
        metadata_backend = con.execute(sql_query)
        if metadata_backend.rowcount > 0:
            return True

    return False


def migrate(engine):
    """Replace 'backend' with 'store' in meta_data column of image_locations"""
    sql_query = ("UPDATE image_locations SET meta_data = REPLACE(meta_data, "
                 "'\"backend\":', '\"store\":') where INSTR(meta_data, "
                 " '\"backend\":') > 0")

    # NOTE(abhishekk): INSTR function doesn't supported in postgresql
    if engine.name == 'postgresql':
        sql_query = ("UPDATE image_locations SET meta_data = REPLACE("
                     "meta_data, '\"backend\":', '\"store\":') where "
                     "POSITION('\"backend\":' IN meta_data) > 0")

    with engine.connect() as con:
        migrated_rows = con.execute(sql_query)
        return migrated_rows.rowcount
