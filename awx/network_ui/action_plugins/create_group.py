#---- create_group

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
        the_list = self._task.args.get('list', None)
        list_var = self._task.args.get('list_var', None)

        id = self._task.args.get('id', None)
        name = self._task.args.get('name', None)
        x1 = self._task.args.get('x1', None)
        y1 = self._task.args.get('y1', None)
        x2 = self._task.args.get('x2', None)
        y2 = self._task.args.get('y2', None)
        topology = self._task.args.get('topology', None)
        group_type = self._task.args.get('group_type', None)

        inventory_group_id = self._task.args.get('inventory_group_id', 0)

        url = server + '/api/v2/canvas/group/'
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(dict(id=id,
                                                           name=name,
                                                           x1=x1,
                                                           y1=y1,
                                                           x2=x2,
                                                           y2=y2,
                                                           topology=topology,
                                                           group_type=group_type,
                                                           inventory_group_id=inventory_group_id,
                                                           )),
                                 verify=False,
                                 auth=(user, password),
                                 headers=headers)
        if var is not None:
            result['ansible_facts'] = {var: response.json()}
        elif list_var is not None:
            if the_list is None:
                the_list = []
            the_list.append(response.json())
            result['ansible_facts'] = {list_var: the_list}
        return result
