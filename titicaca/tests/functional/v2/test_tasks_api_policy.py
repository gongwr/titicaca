# Copyright 2021 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from unittest import mock

import oslo_policy.policy
from oslo_serialization import jsonutils

from titicaca.api import policy
from titicaca.tests import functional


TASK1 = {
    "type": "import",
    "input": {
        "import_from": "http://example.com",
        "import_from_format": "qcow2",
        "image_properties": {
            'disk_format': 'vhd',
            'container_format': 'ovf'
        }
    }
}

TASK2 = {
    "type": "api_image_import",
    "input": {
        "import_from": "http://example.com",
        "import_from_format": "qcow2",
        "image_properties": {
            'disk_format': 'vhd',
            'container_format': 'ovf'
        }
    }
}


class TestTasksPolicy(functional.SynchronousAPIBase):
    def setUp(self):
        super(TestTasksPolicy, self).setUp()
        self.policy = policy.Enforcer()

    def set_policy_rules(self, rules):
        self.policy.set_rules(
            oslo_policy.policy.Rules.from_dict(rules),
            overwrite=True)

    def start_server(self):
        with mock.patch.object(policy, 'Enforcer') as mock_enf:
            mock_enf.return_value = self.policy
            super(TestTasksPolicy, self).start_server()

    def _create_task(self, path=None, data=None, expected_code=201):
        if not path:
            path = "/v2/tasks"
        resp = self.api_post(path,
                             json=data)
        task = jsonutils.loads(resp.text)
        self.assertEqual(expected_code, resp.status_code)
        return task

    def load_data(self):
        tasks = []
        for task in [TASK1, TASK2]:
            resp = self._create_task(data=task)
            tasks.append(resp['id'])
            self.assertEqual(task['type'], resp['type'])

        return tasks

    def test_tasks_create_basic(self):
        self.start_server()
        # First make sure create tasks works with default policy
        path = '/v2/tasks'
        task = self._create_task(path=path, data=TASK1)
        self.assertEqual('import', task['type'])

        # Now disable tasks_api_access permissions and make sure any other
        # attempts fail
        self.set_policy_rules({'tasks_api_access': '!'})
        resp = self.api_post(path, json=TASK2)
        self.assertEqual(403, resp.status_code)

    def test_tasks_index_basic(self):
        self.start_server()
        # First make sure  get tasks works with default policy
        tasks = self.load_data()
        path = '/v2/tasks'
        output = self.api_get(path).json
        self.assertEqual(len(tasks), len(output['tasks']))

        # Now disable tasks_api_access permissions and make sure any other
        # attempts fail
        self.set_policy_rules({'tasks_api_access': '!'})
        resp = self.api_get(path)
        self.assertEqual(403, resp.status_code)

    def test_tasks_get_basic(self):
        self.start_server()
        # First make sure  get task works with default policy
        tasks = self.load_data()
        path = '/v2/tasks/%s' % tasks[0]
        task = self.api_get(path).json
        self.assertEqual('import', task['type'])

        # Now disable tasks_api_access permissions and make sure any other
        # attempts fail
        self.set_policy_rules({'tasks_api_access': '!'})
        path = '/v2/tasks/%s' % tasks[1]
        resp = self.api_get(path)
        self.assertEqual(403, resp.status_code)
