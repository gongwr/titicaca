# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

# NOTE(markwash): These functions are used in the base tests cases to
# set up the db api implementation under test. Rather than accessing them
# directly, test modules should use the load and reset functions below.
get_db = None
reset_db = None


def load(get_db_fn, reset_db_fn):
    global get_db, reset_db
    get_db = get_db_fn
    reset_db = reset_db_fn


def reset():
    global get_db, reset_db
    get_db = None
    reset_db = None
