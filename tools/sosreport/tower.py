# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import sos
from distutils.version import LooseVersion

SOSREPORT_TOWER_COMMANDS = [
    "ansible --version",      # ansible core version
    "tower-manage --version", # tower version
    "supervisorctl status",   # tower process status
    "pip list"		          # pip package list
    "tree -d /var/lib/awx",   # show me the dirs
    "ls -ll /var/lib/awx",    # check permissions
    "ls -ll /etc/tower",
]

SOSREPORT_TOWER_DIRS = [
    "/etc/tower/",
    "/var/log/tower",
    "/var/log/httpd",
    "/var/log/apache2",
    "/var/log/redis",
    "/var/log/supervisor",
    "/var/log/syslog",
    "/var/log/udev",
    "/var/log/kern*",
    "/var/log/dist-upgrade",
    "/var/log/installer",
    "/var/log/unattended-upgrades",
    "/var/log/apport.log"
]


if LooseVersion(sos.__version__) >= LooseVersion('3.0'):
    from sos.plugins import Plugin, RedHatPlugin, UbuntuPlugin

    class tower(Plugin, RedHatPlugin, UbuntuPlugin):
        '''Collect Ansible Tower related information'''
        plugin_name = "tower"

        def setup(self):

            for path in SOSREPORT_TOWER_DIRS:
                self.add_copy_spec(path)

            for command in SOSREPORT_TOWER_COMMANDS:
                self.add_cmd_output(command)

else:
    import sos.plugintools

    class tower(sos.plugintools.PluginBase):
        '''Collect Ansible Tower related information'''

        def setup(self):

            for path in SOSREPORT_TOWER_DIRS:
                self.addCopySpec(path)

            for command in SOSREPORT_TOWER_COMMANDS:
                self.collectExtOutput(command)

