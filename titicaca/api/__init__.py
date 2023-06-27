# Copyright 2011-2012 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from oslo_config import cfg
import paste.urlmap

CONF = cfg.CONF


def root_app_factory(loader, global_conf, **local_conf):
    return paste.urlmap.urlmap_factory(loader, global_conf, **local_conf)
