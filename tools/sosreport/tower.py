# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from sos.plugins import Plugin, RedHatPlugin, UbuntuPlugin

SOSREPORT_TOWER_COMMANDS = [
    "awx-manage --version", # tower version
    "awx-manage list_instances", # tower cluster configuration
    "awx-manage run_dispatcher --status", # tower dispatch worker status
    "awx-manage run_callback_receiver --status", # tower callback worker status
    "awx-manage check_license --data", # tower license status
    "awx-manage run_wsbroadcast --status", # tower broadcast websocket status
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
    "/etc/supervisord.d/",
    "/etc/nginx/",
    "/var/log/tower",
    "/var/log/nginx",
    "/var/log/supervisor",
    "/var/log/redis",
    "/etc/opt/rh/rh-redis5/redis.conf",
    "/etc/redis.conf",
    "/var/opt/rh/rh-redis5/log/redis/redis.log",
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


class Tower(Plugin, RedHatPlugin, UbuntuPlugin):
    '''Collect Ansible Tower related information'''
    plugin_name = "tower"

    def setup(self):

        for path in SOSREPORT_TOWER_DIRS:
            self.add_copy_spec(path)

        self.add_forbidden_path(SOSREPORT_FORBIDDEN_PATHS)

        self.add_cmd_output(SOSREPORT_TOWER_COMMANDS)

