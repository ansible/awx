#---- list_link

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

        link_id = self._task.args.get('link_id', None)
        from_device = self._task.args.get('from_device', None)
        to_device = self._task.args.get('to_device', None)
        from_interface = self._task.args.get('from_interface', None)
        to_interface = self._task.args.get('to_interface', None)
        id = self._task.args.get('id', None)
        name = self._task.args.get('name', None)

        filter_data = dict(link_id=link_id,
                           from_device=from_device,
                           to_device=to_device,
                           from_interface=from_interface,
                           to_interface=to_interface,
                           id=id,
                           name=name,
                           )
        filter_data = {x: y for x, y in filter_data.iteritems() if y is not None}

        url = '/api/v2/canvas/link/'
        results = []
        while url is not None:
            url = server + url
            data = requests.get(url, verify=False, auth=(user, password), params=filter_data).json()
            results.extend(data.get('results', []))
            url = data.get('next', None)
        result['ansible_facts'] = {var: results}
        return result
