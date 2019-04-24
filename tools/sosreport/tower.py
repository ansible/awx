# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import sos
from distutils.version import LooseVersion

SOSREPORT_TOWER_COMMANDS = [
    "ansible --version",      # ansible core version
    "awx-manage --version", # tower version
    "awx-manage list_instances", # tower cluster configuration
    "awx-manage run_dispatcher --status", # tower dispatch worker status
    "supervisorctl status",   # tower process status
    "/var/lib/awx/venv/awx/bin/pip freeze",        # pip package list
    "/var/lib/awx/venv/awx/bin/pip freeze -l",     # pip package list without globally-installed packages
    "/var/lib/awx/venv/ansible/bin/pip freeze",    # pip package list
    "/var/lib/awx/venv/ansible/bin/pip freeze -l", # pip package list without globally-installed packages
    "tree -d /var/lib/awx",   # show me the dirs
    "ls -ll /var/lib/awx",    # check permissions
    "ls -ll /var/lib/awx/venv", # list all venvs
    "ls -ll /etc/tower",
    "umask -p"    # check current umask
]

SOSREPORT_TOWER_DIRS = [
    "/etc/tower/",
    "/etc/ansible/",
    "/etc/supervisord.d/",
    "/etc/nginx/",
    "/var/log/tower",
    "/var/log/nginx",
    "/var/log/supervisor",
    "/var/log/syslog",
    "/var/log/udev",
    "/var/log/kern*",
    "/var/log/dist-upgrade",
    "/var/log/installer",
    "/var/log/unattended-upgrades",
    "/var/log/apport.log"
]

SOSREPORT_FORBIDDEN_PATHS = [
    "/etc/tower/SECRET_KEY",
    "/etc/tower/tower.key",
    "/etc/tower/awx.key",
    "/etc/tower/tower.cert",
    "/etc/tower/awx.cert",
    "/var/log/tower/profile"
]

if LooseVersion(sos.__version__) >= LooseVersion('3.0'):
    from sos.plugins import Plugin, RedHatPlugin, UbuntuPlugin

    class tower(Plugin, RedHatPlugin, UbuntuPlugin):
        '''Collect Ansible Tower related information'''
        plugin_name = "tower"

        def setup(self):

            for path in SOSREPORT_TOWER_DIRS:
                self.add_copy_spec(path)

            for path in SOSREPORT_FORBIDDEN_PATHS:
                self.add_forbidden_path(path)

            for command in SOSREPORT_TOWER_COMMANDS:
                self.add_cmd_output(command)

else:
    import sos.plugintools

    class tower(sos.plugintools.PluginBase):
        '''Collect Ansible Tower related information'''

        def setup(self):

            for path in SOSREPORT_TOWER_DIRS:
                self.addCopySpec(path)

            for path in SOSREPORT_FORBIDDEN_PATHS:
                self.addForbiddenPath(path)

            for command in SOSREPORT_TOWER_COMMANDS:
                self.collectExtOutput(command)

