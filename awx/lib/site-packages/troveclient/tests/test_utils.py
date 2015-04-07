# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import six
import testtools
from troveclient import utils


class UtilsTest(testtools.TestCase):

    def test_add_hookable_mixin(self):
        def func():
            pass

        hook_type = "hook_type"
        mixin = utils.HookableMixin()
        mixin.add_hook(hook_type, func)
        self.assertTrue(hook_type in mixin._hooks_map)
        self.assertTrue(func in mixin._hooks_map[hook_type])

    def test_run_hookable_mixin(self):
        def func():
            pass

        hook_type = "hook_type"
        mixin = utils.HookableMixin()
        mixin.add_hook(hook_type, func)
        mixin.run_hooks(hook_type)

    def test_environment(self):
        self.assertEqual('', utils.env())
        self.assertEqual('passing', utils.env(default='passing'))

        os.environ['test_abc'] = 'passing'
        self.assertEqual('passing', utils.env('test_abc'))
        self.assertEqual('', utils.env('test_abcd'))

    def test_slugify(self):
        import unicodedata  # noqa

        self.assertEqual('not_unicode', utils.slugify('not_unicode'))
        self.assertEqual('unicode', utils.slugify(six.u('unicode')))
        self.assertEqual('slugify-test', utils.slugify('SLUGIFY% test!'))
