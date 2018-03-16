{%for model in models-%}
{%-if model.api-%}
#---- delete_{{model.name.lower()}}

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

{%for field in model.fields%}{%if field.pk%}
        {{field.name}} = self._task.args.get('{{field.name}}', None){%endif%}{%endfor%}

        url = server + '{{model.v2_end_point}}' + str({%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}) + '/'
        requests.delete(url,
                        verify=False,
                        auth=(user, password))
        return result

{%endif%}
{%endfor%}
