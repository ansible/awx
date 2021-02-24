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

    BASE_DIR = '/tmp'

    bwrap_pattern = 'bwrap_[0-9]*_*'
    private_data_dir_pattern = 'awx_[0-9]*_*'

    bwrap_path_pattern = os.path.join(BASE_DIR, bwrap_pattern)

    for bwrap_path in glob.iglob(bwrap_path_pattern):
        st = os.stat(bwrap_path)
        modtime = datetime.datetime.fromtimestamp(st.st_mtime)

        if modtime > job_cutoff:
            continue
        elif modtime > folder_cutoff:
            private_data_dir_path_pattern = os.path.join(BASE_DIR, bwrap_path, private_data_dir_pattern)
            private_data_dir_path = next(glob.iglob(private_data_dir_path_pattern), None)
            if private_data_dir_path:
                try:
                    if subprocess.check_call(['ansible-runner', 'is-alive', private_data_dir_path]) == 0:
                        continue
                except subprocess.CalledProcessError:
                    # the job isn't running anymore, clean up this path
                    module.debug('Deleting path {} its job has completed.'.format(bwrap_path))
            module.debug('Deleting path {} due to private_data_dir not being found.'.format(bwrap_path))
        else:
            module.debug('Deleting path {} because modification date is too old.'.format(bwrap_path))
        changed = True
        paths_removed.add(bwrap_path)
        shutil.rmtree(bwrap_path)

    module.exit_json(changed=changed, paths_removed=list(paths_removed))


if __name__ == '__main__':
    main()
