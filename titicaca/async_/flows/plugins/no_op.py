# Copyright 2017 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from oslo_config import cfg
from oslo_log import log as logging
from taskflow.patterns import linear_flow as lf
from taskflow import task

LOG = logging.getLogger(__name__)

CONF = cfg.CONF


class _Noop(task.Task):

    def __init__(self, task_id, task_type, image_repo):
        self.task_id = task_id
        self.task_type = task_type
        self.image_repo = image_repo
        super(_Noop, self).__init__(
            name='%s-Noop-%s' % (task_type, task_id))

    def execute(self, **kwargs):

        LOG.debug("No_op import plugin")
        return

    def revert(self, result=None, **kwargs):
        # NOTE(flaper87): If result is None, it probably
        # means this task failed. Otherwise, we would have
        # a result from its execution.
        if result is not None:
            LOG.debug("No_op import plugin failed")
            return


def get_flow(**kwargs):
    """Return task flow for no-op.

    :param task_id: Task ID.
    :param task_type: Type of the task.
    :param image_repo: Image repository used.
    """
    task_id = kwargs.get('task_id')
    task_type = kwargs.get('task_type')
    image_repo = kwargs.get('image_repo')

    return lf.Flow(task_type).add(
        _Noop(task_id, task_type, image_repo),
    )
