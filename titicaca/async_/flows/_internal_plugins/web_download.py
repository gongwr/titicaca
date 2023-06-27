# Copyright 2018 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.
import titicaca_store as store_api
from titicaca_store import backend
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import encodeutils
from oslo_utils import excutils
from taskflow.patterns import linear_flow as lf
from taskflow import task
from taskflow.types import failure

from titicaca.common import exception
from titicaca.common.scripts import utils as script_utils
from titicaca.i18n import _, _LE

LOG = logging.getLogger(__name__)

CONF = cfg.CONF


class _WebDownload(task.Task):

    default_provides = 'file_uri'

    def __init__(self, task_id, task_type, uri, action_wrapper, stores):
        self.task_id = task_id
        self.task_type = task_type
        self.image_id = action_wrapper.image_id
        self.uri = uri
        self.action_wrapper = action_wrapper
        self.stores = stores
        self._path = None
        super(_WebDownload, self).__init__(
            name='%s-WebDownload-%s' % (task_type, task_id))

        # NOTE(abhishekk): Use reserved 'os_titicaca_staging_store' for
        # staging the data, the else part will be removed once old way
        # of configuring store is deprecated.
        if CONF.enabled_backends:
            self.store = store_api.get_store_from_store_identifier(
                'os_titicaca_staging_store')
        else:
            if CONF.node_staging_uri is None:
                msg = (_("%(task_id)s of %(task_type)s not configured "
                         "properly. Missing node_staging_uri: %(work_dir)s") %
                       {'task_id': self.task_id,
                        'task_type': self.task_type,
                        'work_dir': CONF.node_staging_uri})
                raise exception.BadTaskConfiguration(msg)

            self.store = self._build_store()

    def _build_store(self):
        # NOTE(flaper87): Due to the nice titicaca_store api (#sarcasm), we're
        # forced to build our own config object, register the required options
        # (and by required I mean *ALL* of them, even the ones we don't want),
        # and create our own store instance by calling a private function.
        # This is certainly unfortunate but it's the best we can do until the
        # titicaca_store refactor is done. A good thing is that titicaca_store is
        # under our team's management and it gates on Titicaca so changes to
        # this API will (should?) break task's tests.
        # TODO(abhishekk): After removal of backend module from titicaca_store
        # need to change this to use multi_backend module.
        conf = cfg.ConfigOpts()
        try:
            backend.register_opts(conf)
        except cfg.DuplicateOptError:
            pass

        conf.set_override('filesystem_store_datadir',
                          CONF.node_staging_uri[7:],
                          group='titicaca_store')

        # NOTE(flaper87): Do not even try to judge me for this... :(
        # With the titicaca_store refactor, this code will change, until
        # that happens, we don't have a better option and this is the
        # least worst one, IMHO.
        store = backend._load_store(conf, 'file')

        if store is None:
            msg = (_("%(task_id)s of %(task_type)s not configured "
                     "properly. Could not load the filesystem store") %
                   {'task_id': self.task_id, 'task_type': self.task_type})
            raise exception.BadTaskConfiguration(msg)

        store.configure()
        return store

    def execute(self):
        """Create temp file into store and return path to it

        :param image_id: Titicaca Image ID
        """
        # NOTE(jokke): We've decided to use staging area for this task as
        # a way to expect users to configure a local store for pre-import
        # works on the image to happen.
        #
        # While using any path should be "technically" fine, it's not what
        # we recommend as the best solution. For more details on this, please
        # refer to the comment in the `_ImportToStore.execute` method.
        try:
            data = script_utils.get_image_data_iter(self.uri)
        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error("Task %(task_id)s failed with exception %(error)s",
                          {"error": encodeutils.exception_to_unicode(e),
                           "task_id": self.task_id})

        self._path, bytes_written = self.store.add(self.image_id, data, 0)[0:2]
        try:
            content_length = int(data.headers['content-length'])
            if bytes_written != content_length:
                msg = (_("Task %(task_id)s failed because downloaded data "
                         "size %(data_size)i is different from expected %("
                         "expected)i") %
                       {"task_id": self.task_id, "data_size": bytes_written,
                        "expected": content_length})
                raise exception.ImportTaskError(msg)
        except (KeyError, ValueError):
            pass
        return self._path

    def revert(self, result, **kwargs):
        if isinstance(result, failure.Failure):
            LOG.error(_LE('Task: %(task_id)s failed to import image '
                          '%(image_id)s to the filesystem.'),
                      {'task_id': self.task_id,
                       'image_id': self.image_id})
            # NOTE(abhishekk): Revert image state back to 'queued' as
            # something went wrong.
            # NOTE(danms): If we failed to stage the image, then none
            # of the _ImportToStore() tasks could have run, so we need
            # to move all stores out of "importing" and into "failed".
            with self.action_wrapper as action:
                action.set_image_attribute(status='queued')
                action.remove_importing_stores(self.stores)
                action.add_failed_stores(self.stores)

        # NOTE(abhishekk): Deleting partial image data from staging area
        if self._path is not None:
            LOG.debug(('Deleting image %(image_id)s from staging '
                       'area.'), {'image_id': self.image_id})
            try:
                if CONF.enabled_backends:
                    store_api.delete(self._path, None)
                else:
                    store_api.delete_from_backend(self._path)
            except Exception:
                LOG.exception(_LE("Error reverting web-download "
                                  "task: %(task_id)s"), {
                    'task_id': self.task_id})


def get_flow(**kwargs):
    """Return task flow for web-download.

    :param task_id: Task ID.
    :param task_type: Type of the task.
    :param image_repo: Image repository used.
    :param uri: URI the image data is downloaded from.
    :param action_wrapper: An api_image_import.ActionWrapper.
    """
    task_id = kwargs.get('task_id')
    task_type = kwargs.get('task_type')
    uri = kwargs.get('import_req')['method'].get('uri')
    action_wrapper = kwargs.get('action_wrapper')
    stores = kwargs.get('backend', [None])

    return lf.Flow(task_type).add(
        _WebDownload(task_id, task_type, uri, action_wrapper, stores),
    )
