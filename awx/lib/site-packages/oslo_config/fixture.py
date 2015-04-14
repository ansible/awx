#
# Copyright 2013 Mirantis, Inc.
# Copyright 2013 OpenStack Foundation
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

import fixtures
import six

from oslo_config import cfg


class Config(fixtures.Fixture):
    """Allows overriding configuration settings for the test.

    `conf` will be reset on cleanup.

    """

    def __init__(self, conf=cfg.CONF):
        self.conf = conf

    def setUp(self):
        super(Config, self).setUp()
        # NOTE(morganfainberg): unregister must be added to cleanup before
        # reset is because cleanup works in reverse order of registered items,
        # and a reset must occur before unregistering options can occur.
        self.addCleanup(self._unregister_config_opts)
        self.addCleanup(self.conf.reset)
        self._registered_config_opts = {}

    def config(self, **kw):
        """Override configuration values.

        The keyword arguments are the names of configuration options to
        override and their values.

        If a `group` argument is supplied, the overrides are applied to
        the specified configuration option group, otherwise the overrides
        are applied to the ``default`` group.

        """

        group = kw.pop('group', None)
        for k, v in six.iteritems(kw):
            self.conf.set_override(k, v, group)

    def _unregister_config_opts(self):
        for group in self._registered_config_opts:
            self.conf.unregister_opts(self._registered_config_opts[group],
                                      group=group)

    def register_opt(self, opt, group=None):
        """Register a single option for the test run.

        Options registered in this manner will automatically be unregistered
        during cleanup.

        If a `group` argument is supplied, it will register the new option
        to that group, otherwise the option is registered to the ``default``
        group.
        """
        self.conf.register_opt(opt, group=group)
        self._registered_config_opts.setdefault(group, set()).add(opt)

    def register_opts(self, opts, group=None):
        """Register multiple options for the test run.

        This works in the same manner as register_opt() but takes a list of
        options as the first argument. All arguments will be registered to the
        same group if the ``group`` argument is supplied, otherwise all options
        will be registered to the ``default`` group.
        """
        for opt in opts:
            self.register_opt(opt, group=group)

    def register_cli_opt(self, opt, group=None):
        """Register a single CLI option for the test run.

        Options registered in this manner will automatically be unregistered
        during cleanup.

        If a `group` argument is supplied, it will register the new option
        to that group, otherwise the option is registered to the ``default``
        group.

        CLI options must be registered before the command line and config files
        are parsed. This is to ensure that all CLI options are shown in --help
        and option validation works as expected.
        """
        self.conf.register_cli_opt(opt, group=group)
        self._registered_config_opts.setdefault(group, set()).add(opt)

    def register_cli_opts(self, opts, group=None):
        """Register multiple CLI options for the test run.

        This works in the same manner as register_opt() but takes a list of
        options as the first argument. All arguments will be registered to the
        same group if the ``group`` argument is supplied, otherwise all options
        will be registered to the ``default`` group.

        CLI options must be registered before the command line and config files
        are parsed. This is to ensure that all CLI options are shown in --help
        and option validation works as expected.
        """
        for opt in opts:
            self.register_cli_opt(opt, group=group)
