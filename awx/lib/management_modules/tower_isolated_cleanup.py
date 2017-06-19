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


def main():
    module = AnsibleModule(
        argument_spec = dict(
            cutoff_pk = dict(required=False, default=0, type='int'),
        )
    )
    cutoff_pk = module.params.get('cutoff_pk')
    changed = False
    jobs_removed = set([])

    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=7)

    for search_pattern, extract_pattern in [
        ('/tmp/ansible_tower/jobs/*', r'\/tmp\/ansible_tower\/jobs\/(?P<job_id>\d+)'),
        ('/tmp/ansible_tower_*', r'\/tmp\/ansible_tower_(?P<job_id>\d+)_*'),
        ('/tmp/ansible_tower_proot_*', None),
    ]:
        for path in glob.iglob(search_pattern):
            st = os.stat(path)
            modtime = datetime.datetime.fromtimestamp(st.st_mtime)
            if modtime > cutoff_time:
                # If job's pk value is lower than threshold, we delete it
                try:
                    if extract_pattern is None:
                        continue
                    re_match = re.match(extract_pattern, path)
                    if re_match is None:
                        continue
                    job_id = int(re_match.group('job_id'))
                    if job_id >= cutoff_pk:
                        module.debug('Skipping job {}, which may still be running.'.format(job_id))
                        continue
                except (ValueError, IndexError):
                    continue
            else:
                module.debug('Deleting path {} because modification date is too old.'.format(path))
                job_id = 'unknown'
            changed = True
            jobs_removed.add(job_id)
            if os.path.islink(path):
                os.remove(path)
            else:
                shutil.rmtree(path)

    module.exit_json(changed=changed, jobs_removed=[j for j in jobs_removed])


if __name__ == '__main__':
    main()
