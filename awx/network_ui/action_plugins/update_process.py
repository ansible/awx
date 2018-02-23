#---- update_process

from ansible.plugins.action import ActionBase

import requests
import json


class ActionModule(ActionBase):

    BYPASS_HOST_LOOP = True

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        result = super(ActionModule, self).run(tmp, task_vars)

        server = self._task.args.get('server',
                                     "{0}:{1}".format(self._play_context.remote_addr,
                                                      self._play_context.port))
        user = self._task.args.get('user', self._play_context.remote_user)
        password = self._task.args.get('password', self._play_context.password)

        var = self._task.args.get('var', None)

        process_id = self._task.args.get('process_id', None)
        device = self._task.args.get('device', None)
        name = self._task.args.get('name', None)
        process_type = self._task.args.get('process_type', None)
        id = self._task.args.get('id', None)

        url = server + '/api/v2/canvas/process/' + str(process_id) + '/'
        headers = {'content-type': 'application/json'}
        data = dict(device=device,
                    name=name,
                    process_type=process_type,
                    id=id,
                    )
        data = {x: y for x, y in data.iteritems() if y is not None}
        response = requests.patch(url,
                                  data=json.dumps(data),
                                  verify=False,
                                  auth=(user, password),
                                  headers=headers)
        result['ansible_facts'] = {var: response.json()}
        return result
