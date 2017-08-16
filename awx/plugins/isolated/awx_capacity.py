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

from ansible.module_utils.basic import AnsibleModule

import subprocess


def main():
    module = AnsibleModule(
        argument_spec = dict()
    )
    try:
        version = subprocess.check_output(
            ['awx-expect', '--version'],
            stderr=subprocess.STDOUT
        ).strip()
    except subprocess.CalledProcessError as e:
        module.fail_json(msg=str(e))
        return
    # Duplicated with awx.main.utils.common.get_system_task_capacity
    try:
        out = subprocess.check_output(['free', '-m'])
    except subprocess.CalledProcessError as e:
        module.fail_json(msg=str(e))
        return
    total_mem_value = out.split()[7]
    if int(total_mem_value) <= 2048:
        cap = 50
    cap = 50 + ((int(total_mem_value) / 1024) - 2) * 75

    # Module never results in a change
    module.exit_json(changed=False, capacity=cap, version=version)


if __name__ == '__main__':
    main()
