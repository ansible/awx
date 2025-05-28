from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import re

import requests

from ansible.plugins.action import ActionBase

DEFAULT_OIDC_ENDPOINT = 'https://sso.redhat.com/auth/realms/redhat-external'


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

    def _obtain_auth_token(self, oidc_endpoint, client_id, client_secret):
        if oidc_endpoint.endswith('/'):
            oidc_endpoint = oidc_endpoint.rstrip('/')
        main_url = oidc_endpoint + '/.well-known/openid-configuration'
        response = requests.get(url=main_url, headers={'Accept': 'application/json'})
        data = {}
        if response.status_code != 200:
            data['failed'] = True
            data['msg'] = 'Expected {} to return a status code of 200 but returned status code "{}" instead with content "{}".'.format(
                main_url, response.status_code, response.content
            )
            return data

        auth_url = response.json().get('token_endpoint', None)
        data = {
            'grant_type': 'client_credentials',
            'scope': 'api.console',
            'client_id': client_id,
            'client_secret': client_secret,
        }
        response = requests.post(url=auth_url, data=data)

        if response.status_code != 200:
            data['failed'] = True
            data['msg'] = 'Expected {} to return a status code of 200 but returned status code "{}" instead with content "{}".'.format(
                auth_url, response.status_code, response.content
            )
        else:
            data['token'] = response.json().get('access_token', None)
            data['token_type'] = response.json().get('token_type', None)
        return data

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False

        session = requests.Session()
        result = super(ActionModule, self).run(tmp, task_vars)

        insights_url = self._task.args.get('insights_url', None)
        proj_path = self._task.args.get('project_path', None)
        license = self._task.args.get('awx_license_type', None)
        awx_version = self._task.args.get('awx_version', None)
        authentication = self._task.args.get('authentication', None)
        username = self._task.args.get('username', None)
        password = self._task.args.get('password', None)
        client_id = self._task.args.get('client_id', None)
        client_secret = self._task.args.get('client_secret', None)
        oidc_endpoint = self._task.args.get('oidc_endpoint', DEFAULT_OIDC_ENDPOINT)

        session.headers.update(
            {
                'Content-Type': 'application/json',
                'User-Agent': '{} {} ({})'.format('AWX' if license == 'open' else 'Red Hat Ansible Automation Platform', awx_version, license),
            }
        )

        if authentication == 'service_account' or (client_id and client_secret):
            data = self._obtain_auth_token(oidc_endpoint, client_id, client_secret)
            if 'token' not in data:
                result['failed'] = data['failed']
                result['msg'] = data['msg']
                return result
            session.headers.update({'Authorization': f'{data["token_type"]} {data["token"]}'})
        elif authentication == 'basic' or (username and password):
            session.auth = requests.auth.HTTPBasicAuth(username, password)

        url = '/api/remediations/v1/remediations'
        while url:
            res = session.get('{}{}'.format(insights_url, url), timeout=120)

            if res.status_code != 200:
                result['failed'] = True
                result['msg'] = 'Expected {} to return a status code of 200 but returned status code "{}" instead with content "{}".'.format(
                    url, res.status_code, res.content
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
                playbook_url = '{}/api/remediations/v1/remediations/{}/playbook'.format(insights_url, item['id'])
                res = session.get(playbook_url, timeout=120)
                if res.status_code == 204:
                    continue
                elif res.status_code != 200:
                    result['failed'] = True
                    result['msg'] = 'Expected {} to return a status code of 200 but returned status code "{}" instead with content "{}".'.format(
                        playbook_url, res.status_code, res.content
                    )
                    return result
                self.save_playbook(proj_path, item, res.content)

        self.write_version(proj_path, version)

        result['changed'] = True
        result['version'] = version
        return result
