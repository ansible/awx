from io import StringIO
import json
from django.core.management import call_command
from django.test import TestCase, override_settings


settings_dict = {
    "AUTH_LDAP_1_SERVER_URI": "SERVER_URI",
    "AUTH_LDAP_1_BIND_DN": "BIND_DN",
    "AUTH_LDAP_1_BIND_PASSWORD": "BIND_PASSWORD",
    "AUTH_LDAP_1_GROUP_SEARCH": ["GROUP_SEARCH"],
    "AUTH_LDAP_1_GROUP_TYPE": "string object",
    "AUTH_LDAP_1_GROUP_TYPE_PARAMS": {"member_attr": "member", "name_attr": "cn"},
    "AUTH_LDAP_1_USER_DN_TEMPLATE": "USER_DN_TEMPLATE",
    "AUTH_LDAP_1_USER_SEARCH": ["USER_SEARCH"],
    "AUTH_LDAP_1_USER_ATTR_MAP": {
        "email": "email",
        "last_name": "last_name",
        "first_name": "first_name",
    },
    "AUTH_LDAP_1_CONNECTION_OPTIONS": {},
    "AUTH_LDAP_1_START_TLS": None,
}


@override_settings(**settings_dict)
class TestDumpAuthConfigCommand(TestCase):
    def setUp(self):
        super().setUp()
        self.expected_config = [
            {
                "type": "ansible_base.authentication.authenticator_plugins.ldap",
                "name": "LDAP_1",
                "enabled": True,
                "create_objects": True,
                "users_unique": False,
                "remove_users": True,
                "configuration": {
                    "SERVER_URI": ["SERVER_URI"],
                    "BIND_DN": "BIND_DN",
                    "BIND_PASSWORD": "BIND_PASSWORD",
                    "CONNECTION_OPTIONS": {},
                    "GROUP_TYPE": "str",
                    "GROUP_TYPE_PARAMS": {"member_attr": "member", "name_attr": "cn"},
                    "GROUP_SEARCH": ["GROUP_SEARCH"],
                    "START_TLS": None,
                    "USER_DN_TEMPLATE": "USER_DN_TEMPLATE",
                    "USER_ATTR_MAP": {"email": "email", "last_name": "last_name", "first_name": "first_name"},
                    "USER_SEARCH": ["USER_SEARCH"],
                },
            },
        ]

    def test_json_returned_from_cmd(self):
        output = StringIO()
        call_command("dump_auth_config", stdout=output)
        cmmd_output = json.loads(output.getvalue())

        # check configured LDAP return
        assert cmmd_output[2] == self.expected_config[1]

        # check unconfigured LDAP return
        assert "LDAP_0_missing_fields" in cmmd_output[1]
        assert cmmd_output[1]["LDAP_0_missing_fields"] == ['SERVER_URI', 'GROUP_TYPE', 'GROUP_TYPE_PARAMS', 'USER_DN_TEMPLATE', 'USER_ATTR_MAP']
