# Copyright 2012 IBM Corp.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from novaclient import base


class Coverage(base.Resource):
    def __repr__(self):
        return "<Coverage: %s>" % self.name


class CoverageManager(base.Manager):

    resource_class = Coverage

    def start(self, combine=False, **kwargs):
        body = {'start': {}}
        if combine:
            body['start'] = {'combine': True}
        self.run_hooks('modify_body_for_action', body)
        url = '/os-coverage/action'
        return self.api.client.post(url, body=body)

    def stop(self):
        body = {'stop': {}}
        self.run_hooks('modify_body_for_action', body)
        url = '/os-coverage/action'
        return self.api.client.post(url, body=body)

    def report(self, filename, xml=False, html=False):
        body = {
            'report': {
                'file': filename,
            }
        }
        if xml:
            body['report']['xml'] = True
        elif html:
            body['report']['html'] = True
        self.run_hooks('modify_body_for_action', body)
        url = '/os-coverage/action'
        return self.api.client.post(url, body=body)

    def reset(self):
        body = {'reset': {}}
        self.run_hooks('modify_body_for_action', body)
        url = '/os-coverage/action'
        return self.api.client.post(url, body=body)
