from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False
        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = result['failed'] = False
        result['msg'] = ''
        self._display.deprecated("Mercurial support is deprecated")
        return result
