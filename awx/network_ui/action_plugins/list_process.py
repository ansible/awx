#---- list_process

from ansible.plugins.action import ActionBase

import requests


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
        type = self._task.args.get('type', None)
        id = self._task.args.get('id', None)

        filter_data = dict(process_id=process_id,
                           device=device,
                           name=name,
                           type=type,
                           id=id,
                           )
        filter_data = {x: y for x, y in filter_data.iteritems() if y is not None}

        url = '/api/v2/canvas/process/'
        results = []
        while url is not None:
            url = server + url
            data = requests.get(url, verify=False, auth=(user, password), params=filter_data).json()
            results.extend(data.get('results', []))
            url = data.get('next', None)
        result['ansible_facts'] = {var: results}
        return result
