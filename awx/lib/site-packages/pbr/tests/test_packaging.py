# Copyright (c) 2013 New Dream Network, LLC (DreamHost)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Copyright (C) 2013 Association of Universities for Research in Astronomy
#                    (AURA)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided
#        with the distribution.
#
#     3. The name of AURA and its representatives may not be used to
#        endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY AURA ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL AURA BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS

import os

import fixtures
import mock

from pbr import packaging
from pbr.tests import base


class TestPackagingInGitRepoWithCommit(base.BaseTestCase):

    def setUp(self):
        super(TestPackagingInGitRepoWithCommit, self).setUp()
        self.useFixture(fixtures.TempHomeDir())
        self._run_cmd(
            'git', ['config', '--global', 'user.email', 'nobody@example.com'])
        self._run_cmd('git', ['init', '.'])
        self._run_cmd('git', ['add', '.'])
        self._run_cmd('git', ['commit', '-m', 'test commit'])
        self.run_setup('sdist')
        return

    def test_authors(self):
        # One commit, something should be in the authors list
        with open(os.path.join(self.package_dir, 'AUTHORS'), 'r') as f:
            body = f.read()
        self.assertNotEqual(body, '')

    def test_changelog(self):
        with open(os.path.join(self.package_dir, 'ChangeLog'), 'r') as f:
            body = f.read()
        # One commit, something should be in the ChangeLog list
        self.assertNotEqual(body, '')


class TestPackagingInGitRepoWithoutCommit(base.BaseTestCase):

    def setUp(self):
        super(TestPackagingInGitRepoWithoutCommit, self).setUp()
        self._run_cmd('git', ['init', '.'])
        self._run_cmd('git', ['add', '.'])
        self.run_setup('sdist')
        return

    def test_authors(self):
        # No commits, no authors in list
        with open(os.path.join(self.package_dir, 'AUTHORS'), 'r') as f:
            body = f.read()
        self.assertEqual(body, '\n')

    def test_changelog(self):
        # No commits, nothing should be in the ChangeLog list
        with open(os.path.join(self.package_dir, 'ChangeLog'), 'r') as f:
            body = f.read()
        self.assertEqual(body, 'CHANGES\n=======\n\n')


class TestPackagingInPlainDirectory(base.BaseTestCase):

    def setUp(self):
        super(TestPackagingInPlainDirectory, self).setUp()
        self.run_setup('sdist')
        return

    def test_authors(self):
        # Not a git repo, no AUTHORS file created
        filename = os.path.join(self.package_dir, 'AUTHORS')
        self.assertFalse(os.path.exists(filename))

    def test_changelog(self):
        # Not a git repo, no ChangeLog created
        filename = os.path.join(self.package_dir, 'ChangeLog')
        self.assertFalse(os.path.exists(filename))


class TestPresenceOfGit(base.BaseTestCase):

    def testGitIsInstalled(self):
        with mock.patch.object(packaging,
                               '_run_shell_command') as _command:
            _command.return_value = 'git version 1.8.4.1'
            self.assertEqual(True, packaging._git_is_installed())

    def testGitIsNotInstalled(self):
        with mock.patch.object(packaging,
                               '_run_shell_command') as _command:
            _command.side_effect = OSError
            self.assertEqual(False, packaging._git_is_installed())
