# Copyright (c) 2023 WenRui Gong
# All rights reserved.

# NOTE(rosmaita): This file implements the migration interface, but doesn't
# migrate any data.  The pike01 migration is contract-only.


def has_migrations(engine):
    """Returns true if at least one data row can be migrated."""

    return False


def migrate(engine):
    """Return the number of rows migrated."""

    return 0
