from __future__ import absolute_import, division, print_function

__metaclass__ = type

from .controller_api import ControllerModule
from ansible.module_utils.basic import missing_required_lib

try:
    from awxkit.api.client import Connection
    from awxkit.api.pages.api import ApiV2
    from awxkit.api import get_registered_page

    HAS_AWX_KIT = True
except ImportError:
    HAS_AWX_KIT = False


class ControllerAWXKitModule(ControllerModule):
    connection = None
    apiV2Ref = None

    def __init__(self, argument_spec, **kwargs):
        kwargs['supports_check_mode'] = False

        super().__init__(argument_spec=argument_spec, **kwargs)

        # Die if we don't have AWX_KIT installed
        if not HAS_AWX_KIT:
            self.fail_json(msg=missing_required_lib('awxkit'))

        # Establish our conneciton object
        self.connection = Connection(self.host, verify=self.verify_ssl)

    def authenticate(self):
        try:
            if self.oauth_token:
                self.connection.login(None, None, token=self.oauth_token)
                self.authenticated = True
            elif self.username:
                self.connection.login(username=self.username, password=self.password)
                self.authenticated = True
        except Exception:
            self.fail_json("Failed to authenticate")

    def get_api_v2_object(self):
        if not self.apiV2Ref:
            if not self.authenticated:
                self.authenticate()
            v2_index = get_registered_page('/api/v2/')(self.connection).get()
            self.api_ref = ApiV2(connection=self.connection, **{'json': v2_index})
        return self.api_ref

    def logout(self):
        if self.authenticated:
            self.connection.logout()
