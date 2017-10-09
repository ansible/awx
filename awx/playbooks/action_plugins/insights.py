from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import requests

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def save_playbook(self, proj_path, plan, content):
        fname = '{}-{}.yml'.format(plan.get('name', None) or 'insights-plan', plan['maintenance_id'])
        file_path = os.path.join(proj_path, fname)
        with open(file_path, 'w') as f:
            f.write(content)

    def is_stale(self, proj_path, etag):
        file_path = os.path.join(proj_path, '.version')
        try:
            f = open(file_path, 'r')
            version = f.read()
            f.close()
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

        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(username, password)
        headers = {'Content-Type': 'application/json'}
        
        url = '{}/r/insights/v3/maintenance?ansible=true'.format(insights_url)

        res = session.get(url, headers=headers, timeout=120)

        if res.status_code != 200:
            result['failed'] = True
            result['msg'] = (
                'Expected {} to return a status code of 200 but returned status '
                'code "{}" instead with content "{}".'.format(url, res.status_code, res.content)
            )
            return result

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

        for item in res.json():
            url = '{}/r/insights/v3/maintenance/{}/playbook'.format(insights_url, item['maintenance_id'])
            res = session.get(url, timeout=120)
            if res.status_code != 200:
                result['failed'] = True
                result['msg'] = (
                    'Expected {} to return a status code of 200 but returned status '
                    'code "{}" instead with content "{}".'.format(url, res.status_code, res.content)
                )
                return result
            self.save_playbook(proj_path, item, res.content)

        self.write_version(proj_path, version)

        result['changed'] = True
        result['version'] = version
        return result
