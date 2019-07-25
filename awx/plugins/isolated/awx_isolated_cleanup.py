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

import glob
import os
import re
import shutil
import datetime
import subprocess


def main():
    module = AnsibleModule(
        argument_spec = dict()
    )
    changed = False
    paths_removed = set([])

    # If a folder was last modified before this datetime, it will always be deleted
    folder_cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
    # If a folder does not have an associated job running and is older than
    # this datetime, then it will be deleted because its job has finished
    job_cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)

    for search_pattern in [
        '/tmp/awx_[0-9]*_*', '/tmp/ansible_runner_pi_*',
    ]:
        for path in glob.iglob(search_pattern):
            st = os.stat(path)
            modtime = datetime.datetime.fromtimestamp(st.st_mtime)

            if modtime > job_cutoff:
                continue
            elif modtime > folder_cutoff:
                try:
                    re_match = re.match(r'\/tmp\/awx_\d+_.+', path)
                    if re_match is not None:
                        try:
                            if subprocess.check_call(['ansible-runner', 'is-alive', path]) == 0:
                                continue
                        except subprocess.CalledProcessError:
                            # the job isn't running anymore, clean up this path
                            module.debug('Deleting path {} its job has completed.'.format(path))
                except (ValueError, IndexError):
                    continue
            else:
                module.debug('Deleting path {} because modification date is too old.'.format(path))
            changed = True
            paths_removed.add(path)
            shutil.rmtree(path)

    module.exit_json(changed=changed, paths_removed=list(paths_removed))


if __name__ == '__main__':
    main()
