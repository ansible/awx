#---- update_group

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

        group_id = self._task.args.get('group_id', None)
        id = self._task.args.get('id', None)
        name = self._task.args.get('name', None)
        x1 = self._task.args.get('x1', None)
        y1 = self._task.args.get('y1', None)
        x2 = self._task.args.get('x2', None)
        y2 = self._task.args.get('y2', None)
        topology = self._task.args.get('topology', None)
        type = self._task.args.get('type', None)

        url = server + '/api/v2/canvas/group/' + str(group_id) + '/'
        headers = {'content-type': 'application/json'}
        data = dict(id=id,
                    name=name,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    topology=topology,
                    type=type,
                    )
        data = {x: y for x, y in data.iteritems() if y is not None}
        response = requests.patch(url,
                                  data=json.dumps(data),
                                  verify=False,
                                  auth=(user, password),
                                  headers=headers)
        result['ansible_facts'] = {var: response.json()}
        return result
