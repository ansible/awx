#---- update_topology

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

        topology_id = self._task.args.get('topology_id', None)
        name = self._task.args.get('name', None)
        scale = self._task.args.get('scale', None)
        panX = self._task.args.get('panX', None)
        panY = self._task.args.get('panY', None)
        device_id_seq = self._task.args.get('device_id_seq', None)
        link_id_seq = self._task.args.get('link_id_seq', None)
        group_id_seq = self._task.args.get('group_id_seq', None)
        stream_id_seq = self._task.args.get('stream_id_seq', None)

        url = server + '/api/v2/canvas/topology/' + str(topology_id) + '/'
        headers = {'content-type': 'application/json'}
        data = dict(name=name,
                    scale=scale,
                    panX=panX,
                    panY=panY,
                    device_id_seq=device_id_seq,
                    link_id_seq=link_id_seq,
                    group_id_seq=group_id_seq,
                    stream_id_seq=stream_id_seq,
                    )
        data = {x: y for x, y in data.iteritems() if y is not None}
        response = requests.patch(url,
                                  data=json.dumps(data),
                                  verify=False,
                                  auth=(user, password),
                                  headers=headers)
        result['ansible_facts'] = {var: response.json()}
        return result
