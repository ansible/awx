# Copyright (c) 2016 Ansible by Red Hat, Inc.
#
# This file is part of Ansible Tower, but depends on code imported from Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)

# Python
import atexit
import glob
import os
import pwd

# PSUtil
import psutil

__all__ = []

main_pid = os.getpid()


@atexit.register
def terminate_ssh_control_masters():
    # Only run this cleanup from the main process.
    if os.getpid() != main_pid:
        return
    # Determine if control persist is being used and if any open sockets
    # exist after running the playbook.
    cp_path = os.environ.get('ANSIBLE_SSH_CONTROL_PATH', '')
    if not cp_path:
        return
    cp_dir = os.path.dirname(cp_path)
    if not os.path.exists(cp_dir):
        return
    cp_pattern = os.path.join(cp_dir, 'ansible-ssh-*')
    cp_files = glob.glob(cp_pattern)
    if not cp_files:
        return

    # Attempt to find any running control master processes.
    username = pwd.getpwuid(os.getuid())[0]
    ssh_cm_procs = []
    for proc in psutil.process_iter():
        try:
            pname = proc.name()
            pcmdline = proc.cmdline()
            pusername = proc.username()
        except psutil.NoSuchProcess:
            continue
        if pusername != username:
            continue
        if pname != 'ssh':
            continue
        for cp_file in cp_files:
            if pcmdline and cp_file in pcmdline[0]:
                ssh_cm_procs.append(proc)
                break

    # Terminate then kill control master processes.  Workaround older
    # version of psutil that may not have wait_procs implemented.
    for proc in ssh_cm_procs:
        try:
            proc.terminate()
        except psutil.NoSuchProcess:
            continue
    procs_gone, procs_alive = psutil.wait_procs(ssh_cm_procs, timeout=5)
    for proc in procs_alive:
        proc.kill()
