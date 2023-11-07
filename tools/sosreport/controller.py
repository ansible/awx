# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

try:
    from sos.plugins import Plugin, RedHatPlugin
except ImportError:
    from sos.report.plugins import Plugin, RedHatPlugin

SOSREPORT_CONTROLLER_COMMANDS = [
    "awx-manage --version",  # controller version
    "awx-manage list_instances",  # controller cluster configuration
    "awx-manage run_dispatcher --status",  # controller dispatch worker status
    "awx-manage run_callback_receiver --status",  # controller callback worker status
    "awx-manage check_license --data",  # controller license status
    "awx-manage run_wsbroadcast --status",  # controller broadcast websocket status
    "supervisorctl status",  # controller process status
    "/var/lib/awx/venv/awx/bin/pip freeze",  # pip package list
    "/var/lib/awx/venv/awx/bin/pip freeze -l",  # pip package list without globally-installed packages
    "/var/lib/awx/venv/ansible/bin/pip freeze",  # pip package list
    "/var/lib/awx/venv/ansible/bin/pip freeze -l",  # pip package list without globally-installed packages
    "tree -d /var/lib/awx",  # show me the dirs
    "ls -ll /var/lib/awx",  # check permissions
    "ls -ll /var/lib/awx/venv",  # list all venvs
    "ls -ll /etc/tower",
    "ls -ll /var/run/awx-receptor",  # list contents of dirctory where receptor socket should be
    "ls -ll /etc/receptor",
    "receptorctl --socket /var/run/awx-receptor/receptor.sock status",  # Get information about the status of the mesh
    "umask -p",  # check current umask
]

SOSREPORT_CONTROLLER_DIRS = [
    "/etc/tower/",
    "/etc/receptor/",
    "/etc/supervisord.conf",
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
    "/var/log/apport.log",
]

SOSREPORT_FORBIDDEN_PATHS = [
    "/etc/tower/SECRET_KEY",
    "/etc/tower/tower.key",
    "/etc/tower/awx.key",
    "/etc/tower/tower.cert",
    "/etc/tower/awx.cert",
    "/var/log/tower/profile",
    "/etc/receptor/tls/ca/*.key",
    "/etc/receptor/tls/*.key",
]


class Controller(Plugin, RedHatPlugin):
    '''Collect Ansible Automation Platform controller information'''

    plugin_name = "controller"
    short_desc = "Ansible Automation Platform controller information"

    def setup(self):

        for path in SOSREPORT_CONTROLLER_DIRS:
            self.add_copy_spec(path)

        for path in SOSREPORT_FORBIDDEN_PATHS:
            self.add_forbidden_path(path)

        self.add_cmd_output(SOSREPORT_CONTROLLER_COMMANDS)

    def postproc(self):
        # remove database password
        jreg = r"(\s*\'PASSWORD\'\s*:(\s))(?:\"){1,}(.+)(?:\"){1,}"
        repl = r"\1********"
        self.do_path_regex_sub("/etc/tower/conf.d/postgres.py", jreg, repl)

        # remove email password
        jreg = r"(EMAIL_HOST_PASSWORD\s*=)\'(.+)\'"
        repl = r"\1********"
        self.do_path_regex_sub("/etc/tower/settings.py", jreg, repl)

        # remove email password (if customized)
        jreg = r"(EMAIL_HOST_PASSWORD\s*=)\'(.+)\'"
        repl = r"\1********"
        self.do_path_regex_sub("/etc/tower/conf.d/custom.py", jreg, repl)

        # remove websocket secret
        jreg = r"(BROADCAST_WEBSOCKET_SECRET\s*=\s*)\"(.+)\""
        repl = r"\1********"
        self.do_path_regex_sub("/etc/tower/conf.d/channels.py", jreg, repl)
