from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

import requests

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def save_playbook(self, proj_path, remediation, content):
        name = remediation.get('name', None) or 'insights-remediation'
        name = re.sub(r'[^\w\s-]', '', name).strip().lower()
        name = re.sub(r'[-\s]+', '-', name)
        fname = '{}-{}.yml'.format(name, remediation['id'])
        file_path = os.path.join(proj_path, fname)
        with open(file_path, 'wb') as f:
            f.write(content)

    def is_stale(self, proj_path, etag):
        file_path = os.path.join(proj_path, '.version')
        try:
            with open(file_path, 'r') as f:
                version = f.read()
            return version != etag
        except IOError:
            return True

    def write_version(self, proj_path, etag):
        file_path = os.path.join(proj_path, '.version')
        with open(file_path, 'w') as f:
            f.write(etag)

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False

        result = super(ActionModule, self).run(tmp, task_vars)

        insights_url = self._task.args.get('insights_url', None)
        username = self._task.args.get('username', None)
        password = self._task.args.get('password', None)
        proj_path = self._task.args.get('project_path', None)
        license = self._task.args.get('awx_license_type', None)
        awx_version = self._task.args.get('awx_version', None)

        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(username, password)
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': '{} {} ({})'.format(
                'AWX' if license == 'open' else 'Red Hat Ansible Tower',
                awx_version,
                license
            )
        }
        url = '/api/remediations/v1/remediations'
        while url:
            res = session.get('{}{}'.format(insights_url, url), headers=headers, timeout=120)

            if res.status_code != 200:
                result['failed'] = True
                result['msg'] = (
                    'Expected {} to return a status code of 200 but returned status '
                    'code "{}" instead with content "{}".'.format(url, res.status_code, res.content)
                )
                return result

            # FIXME: ETags are (maybe?) not yet supported in the new
            # API, and even if they are we'll need to put some thought
            # into how to deal with them in combination with pagination.
            if 'ETag' in res.headers:
                version = res.headers['ETag']
                if version.startswith('"') and version.endswith('"'):
                    version = version[1:-1]
            else:
                version = "ETAG_NOT_FOUND"

            if not self.is_stale(proj_path, version):
                result['changed'] = False
                result['version'] = version
                return result

            url = res.json()['links']['next']  # will be None if we're on the last page

            for item in res.json()['data']:
                playbook_url = '{}/api/remediations/v1/remediations/{}/playbook'.format(
                    insights_url, item['id'])
                res = session.get(playbook_url, timeout=120)
                if res.status_code == 204:
                    continue
                elif res.status_code != 200:
                    result['failed'] = True
                    result['msg'] = (
                        'Expected {} to return a status code of 200 but returned status '
                        'code "{}" instead with content "{}".'.format(
                            playbook_url, res.status_code, res.content)
                    )
                    return result
                self.save_playbook(proj_path, item, res.content)

        self.write_version(proj_path, version)

        result['changed'] = True
        result['version'] = version
        return result
