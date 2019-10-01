# Copyright (c) 2017 Ansible by Red Hat
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

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule

import subprocess
import os
import psutil


def get_cpu_capacity():
    env_forkcpu = os.getenv('SYSTEM_TASK_FORKS_CPU', None)
    cpu = psutil.cpu_count()

    if env_forkcpu:
        forkcpu = int(env_forkcpu)
    else:
        forkcpu = 4
    return (cpu, cpu * forkcpu)


def get_mem_capacity():
    env_forkmem = os.getenv('SYSTEM_TASK_FORKS_MEM', None)
    if env_forkmem:
        forkmem = int(env_forkmem)
    else:
        forkmem = 100

    mem = psutil.virtual_memory().total
    return (mem, max(1, ((mem / 1024 / 1024) - 2048) / forkmem))


def main():
    module = AnsibleModule(
        argument_spec = dict()
    )

    ar = module.get_bin_path('ansible-runner', required=True)

    try:
        version = subprocess.check_output(
            [ar, '--version'],
            stderr=subprocess.STDOUT
        ).strip()
    except subprocess.CalledProcessError as e:
        module.fail_json(msg=to_text(e))
        return
    # NOTE: Duplicated with awx.main.utils.common capacity utilities
    cpu, capacity_cpu = get_cpu_capacity()
    mem, capacity_mem = get_mem_capacity()

    # Module never results in a change
    module.exit_json(changed=False, capacity_cpu=capacity_cpu,
                     capacity_mem=capacity_mem, version=version,
                     ansible_facts=dict(
                         awx_cpu=cpu,
                         awx_mem=mem,
                         awx_capacity_cpu=capacity_cpu,
                         awx_capacity_mem=capacity_mem,
                         awx_capacity_version=version
                     ))


if __name__ == '__main__':
    main()
