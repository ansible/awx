from io import StringIO
import json
from django.core.management import call_command
from django.test import TestCase, override_settings


# SAML
@override_settings(SOCIAL_AUTH_SAML_SP_ENTITY_ID="SP_ENTITY_ID")
@override_settings(SOCIAL_AUTH_SAML_SP_PUBLIC_CERT="SP_PUBLIC_CERT")
@override_settings(SOCIAL_AUTH_SAML_SP_PRIVATE_KEY="SP_PRIVATE_KEY")
@override_settings(SOCIAL_AUTH_SAML_ORG_INFO="ORG_INFO")
@override_settings(SOCIAL_AUTH_SAML_TECHNICAL_CONTACT="TECHNICAL_CONTACT")
@override_settings(SOCIAL_AUTH_SAML_SUPPORT_CONTACT="SUPPORT_CONTACT")
@override_settings(SOCIAL_AUTH_SAML_SP_EXTRA="SP_EXTRA")
@override_settings(SOCIAL_AUTH_SAML_SECURITY_CONFIG="SECURITY_CONFIG")
@override_settings(SOCIAL_AUTH_SAML_EXTRA_DATA="EXTRA_DATA")
@override_settings(SOCIAL_AUTH_SAML_ENABLED_IDPS="ENABLED_IDPS")

# LDAP
@override_settings(AUTH_LDAP_1_SERVER_URI=["SERVER_URI"])
@override_settings(AUTH_LDAP_1_BIND_DN="BIND_DN")
@override_settings(AUTH_LDAP_1_BIND_PASSWORD="BIND_PASSWORD")
@override_settings(AUTH_LDAP_1_GROUP_SEARCH=["GROUP_SEARCH"])
@override_settings(AUTH_LDAP_1_GROUP_TYPE="string object")
@override_settings(AUTH_LDAP_1_GROUP_TYPE_PARAMS={"member_attr": "member", "name_attr": "cn"})
@override_settings(AUTH_LDAP_1_USER_DN_TEMPLATE="USER_DN_TEMPLATE")
@override_settings(AUTH_LDAP_1_USER_SEARCH=["USER_SEARCH"])
@override_settings(
    AUTH_LDAP_1_USER_ATTR_MAP={
        "email": "email",
        "last_name": "last_name",
        "first_name": "first_name",
    }
)
@override_settings(AUTH_LDAP_1_CONNECTION_OPTIONS={})
@override_settings(AUTH_LDAP_1_START_TLS=None)
class TestDumpAuthConfigCommand(TestCase):
    def setUp(self):
        super().setUp()
        self.expected_config = [
            {
                "type": "awx.authentication.authenticator_plugins.saml",
                "enabled": True,
                "configuration": {
                    "SP_ENTITY_ID": "SP_ENTITY_ID",
                    "SP_PUBLIC_CERT": "SP_PUBLIC_CERT",
                    "SP_PRIVATE_KEY": "SP_PRIVATE_KEY",
                    "ORG_INFO": "ORG_INFO",
                    "TECHNICAL_CONTACT": "TECHNICAL_CONTACT",
                    "SUPPORT_CONTACT": "SUPPORT_CONTACT",
                    "SP_EXTRA": "SP_EXTRA",
                    "SECURITY_CONFIG": "SECURITY_CONFIG",
                    "EXTRA_DATA": "EXTRA_DATA",
                    "ENABLED_IDPS": "ENABLED_IDPS",
                    "CALLBACK_URL": "CALLBACK_URL",
                },
            },
            {
                "type": "awx.authentication.authenticator_plugins.ldap",
                "enabled": True,
                "configuration": {
                    "SERVER_URI": ["SERVER_URI"],
                    "BIND_DN": "BIND_DN",
                    "BIND_PASSWORD": "BIND_PASSWORD",
                    "GROUP_SEARCH": ["GROUP_SEARCH"],
                    "GROUP_TYPE": "string object",
                    "GROUP_TYPE_PARAMS": {"member_attr": "member", "name_attr": "cn"},
                    "USER_DN_TEMPLATE": "USER_DN_TEMPLATE",
                    "USER_SEARCH": ["USER_SEARCH"],
                    "USER_ATTR_MAP": {"email": "email", "last_name": "last_name", "first_name": "first_name"},
                    "CONNECTION_OPTIONS": {},
                    "START_TLS": None,
                },
            },
        ]

    def test_json_returned_from_cmd(self):
        output = StringIO()
        call_command("dump_auth_config", stdout=output)
        assert output.getvalue().rstrip() == json.dumps(self.expected_config)
