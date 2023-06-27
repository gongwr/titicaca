# Copyright (C) 2018 Verizon Wireless
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.


def has_migrations(engine):
    """Returns true if at least one data row can be migrated."""

    return False


def migrate(engine):
    """Return the number of rows migrated."""

    return 0
