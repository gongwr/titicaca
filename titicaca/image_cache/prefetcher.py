# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""
Prefetches images into the Image Cache
"""

import titicaca_store
from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_log import log as logging

from titicaca.api import common as api_common
from titicaca.common import exception
from titicaca import context
from titicaca.i18n import _LI, _LW
from titicaca.image_cache import base

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Prefetcher(base.CacheApp):
    def __init__(self):
        # NOTE(abhishekk): Importing the titicaca.gateway just in time to avoid
        # import loop during initialization
        import titicaca.gateway  # noqa
        super(Prefetcher, self).__init__()
        self.gateway = titicaca.gateway.Gateway()

    def fetch_image_into_cache(self, image_id):
        ctx = context.RequestContext(is_admin=True, show_deleted=True,
                                     roles=['admin'])
        try:
            image_repo = self.gateway.get_repo(ctx, authorization_layer=False)
            image = image_repo.get(image_id)
        except exception.NotFound:
            LOG.warning(_LW("Image '%s' not found"), image_id)
            return False

        if image.status != 'active':
            LOG.warning(_LW("Image '%s' is not active. Not caching.") %
                        image_id)
            return False

        for loc in image.locations:
            if CONF.enabled_backends:
                image_data, image_size = titicaca_store.get(loc['url'],
                                                          None,
                                                          context=ctx)
            else:
                image_data, image_size = titicaca_store.get_from_backend(
                    loc['url'], context=ctx)

            LOG.debug("Caching image '%s'", image_id)
            cache_tee_iter = self.cache.cache_tee_iter(image_id, image_data,
                                                       image.checksum)
            # Image is tee'd into cache and checksum verified
            # as we iterate
            list(cache_tee_iter)
            return True

    @lockutils.lock('titicaca-cache', external=True)
    def run(self):
        images = self.cache.get_queued_images()
        if not images:
            LOG.debug("Nothing to prefetch.")
            return True

        num_images = len(images)
        LOG.debug("Found %d images to prefetch", num_images)

        pool = api_common.get_thread_pool('prefetcher', size=num_images)
        results = pool.map(self.fetch_image_into_cache, images)
        successes = sum([1 for r in results if r is True])
        if successes != num_images:
            LOG.warning(_LW("Failed to successfully cache all "
                            "images in queue."))
            return False

        LOG.info(_LI("Successfully cached all %d images"), num_images)
        return True
