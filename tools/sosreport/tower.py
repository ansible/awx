# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved.

import sos
from distutils.version import LooseVersion

if LooseVersion(sos.__version__) >= LooseVersion('3.0'):
    from sos.plugins import Plugin, RedHatPlugin, UbuntuPlugin

    class tower(Plugin, RedHatPlugin, UbuntuPlugin):
        '''Collect Ansible Tower related information'''
        plugin_name = "tower"

        def setup(self):

            commands = [
                         "ansible --version",      # ansible core version
                         "awx-manage --version",   # tower version
                         "supervisorctl status",   # tower process status
                         "tree -d /var/lib/awx",   # show me the dirs
                         "ls -ll /var/lib/awx",    # check permissions
                         "ls -ll /etc/awx"
                       ]

            dirs = [
                    "/etc/awx/",
                    "/var/log/supervisor/",
                    "/var/log/syslog",
                    "/var/log/udev",
                    "/var/log/kern*",
                    "/var/log/dist-upgrade",
                    "/var/log/installer",
                    "/var/log/unattended-upgrades",
                    "/var/log/apport.log"
               ]

            for path in dirs:
                self.add_copy_spec(path)

            for command in commands:
                self.collect_ext_output(command)

else:
    import sos.plugintools

    class tower(sos.plugintools.PluginBase):
        '''Collect Ansible Tower related information'''

        def setup(self):

            commands = [
                         "ansible --version",      # ansible core version
                         "awx-manage --version",   # tower version
                         "supervisorctl status",   # tower process status
                         "tree -d /var/lib/awx",   # show me the dirs
                         "ls -ll /var/lib/awx",    # check permissions
                         "ls -ll /etc/awx"
                       ]

            dirs = [
                    "/etc/awx/",
                    "/var/log/supervisor/",
                    "/var/log/syslog",
                    "/var/log/udev",
                    "/var/log/kern*",
                    "/var/log/dist-upgrade",
                    "/var/log/installer",
                    "/var/log/unattended-upgrades",
                    "/var/log/apport.log"
               ]

            for path in dirs:
                self.addCopySpec(path)

            for command in commands:
                self.collectExtOutput(command)

