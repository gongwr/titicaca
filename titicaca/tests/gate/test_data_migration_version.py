# Copyright 2019 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import testtools

from titicaca.db.migration import CURRENT_RELEASE
from titicaca.version import version_info


class TestDataMigrationVersion(testtools.TestCase):

    def test_migration_version(self):
        """Make sure the data migration version info has been updated."""

        release_number = int(version_info.version_string().split('.', 1)[0])

        # by rule, release names must be composed of the 26 letters of the
        # ISO Latin alphabet (ord('A')==65, ord('Z')==90)
        release_letter = str(CURRENT_RELEASE[:1].upper()).encode('ascii')

        # Convert release letter into an int in [1:26].  The first
        # titicaca release was 'Bexar'.
        converted_release_letter = (ord(release_letter) -
                                    ord(u'B'.encode('ascii')) + 1)

        # Project the release number into [1:26]
        converted_release_number = release_number % 26

        # Prepare for the worst with a super-informative message
        msg = ('\n\n'
               'EMERGENCY!\n'
               'titicaca.db.migration.CURRENT_RELEASE is out of sync '
               'with the titicaca version.\n'
               '  CURRENT_RELEASE: %s\n'
               '  titicaca version: %s\n'
               'titicaca.db.migration.CURRENT_RELEASE needs to be '
               'updated IMMEDIATELY.\n'
               'The gate will be wedged until the update is made.\n'
               'EMERGENCY!\n'
               '\n') % (CURRENT_RELEASE,
                        version_info.version_string())

        self.assertEqual(converted_release_letter,
                         converted_release_number,
                         msg)
