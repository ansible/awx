from io import StringIO
import json
from django.core.management import call_command
from django.test import TestCase, override_settings


settings_dict = {
    "SOCIAL_AUTH_SAML_SP_ENTITY_ID": "SP_ENTITY_ID",
    "SOCIAL_AUTH_SAML_SP_PUBLIC_CERT": "SP_PUBLIC_CERT",
    "SOCIAL_AUTH_SAML_SP_PRIVATE_KEY": "SP_PRIVATE_KEY",
    "SOCIAL_AUTH_SAML_ORG_INFO": "ORG_INFO",
    "SOCIAL_AUTH_SAML_TECHNICAL_CONTACT": "TECHNICAL_CONTACT",
    "SOCIAL_AUTH_SAML_SUPPORT_CONTACT": "SUPPORT_CONTACT",
    "SOCIAL_AUTH_SAML_SP_EXTRA": "SP_EXTRA",
    "SOCIAL_AUTH_SAML_SECURITY_CONFIG": "SECURITY_CONFIG",
    "SOCIAL_AUTH_SAML_EXTRA_DATA": "EXTRA_DATA",
    "SOCIAL_AUTH_SAML_ENABLED_IDPS": {
        "Keycloak": {
            "attr_last_name": "last_name",
            "attr_groups": "groups",
            "attr_email": "email",
            "attr_user_permanent_id": "name_id",
            "attr_username": "username",
            "entity_id": "https://example.com/auth/realms/awx",
            "url": "https://example.com/auth/realms/awx/protocol/saml",
            "x509cert": "-----BEGIN CERTIFICATE-----\nMIIDDjCCAfYCCQCPBeVvpo8+VzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJV\nUzELMAkGA1UECAwCTkMxDzANBgNVBAcMBkR1cmhhbTEMMAoGA1UECgwDYXd4MQ4w\nDAYDVQQDDAVsb2NhbDAeFw0yNDAxMTgxNDA4MzFaFw0yNTAxMTcxNDA4MzFaMEkx\nCzAJBgNVBAYTAlVTMQswCQYDVQQIDAJOQzEPMA0GA1UEBwwGRHVyaGFtMQwwCgYD\nVQQKDANhd3gxDjAMBgNVBAMMBWxvY2FsMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A\nMIIBCgKCAQEAzouj93oyFXsHEABdPESh3CYpp5QJJBM4TLYIIolk6PFOFIVwBuFY\nfExi5w7Hh4A42lPM6RkrT+u3h7LV39H9MRUfqygOSmaxICTOI0sU9ROHc44fWWzN\n756OP4B5zSiqG82q8X7nYVkcID+2F/3ekPLMOlWn53OrcdfKKDIcqavoTkQJefc2\nggXU3WgVCxGki/qCm+e5cZ1Cpl/ykSLOT8dWMEzDd12kin66zJ3KYz9F2Q5kQTh4\nKRAChnBBoEqzOfENHEAaHALiXOlVSy61VcLbtvskRMMwBtsydlnd9n/HGnktgrid\n3Ca0z5wBTHWjAOBvCKxKJuDa+jmyHEnpcQIDAQABMA0GCSqGSIb3DQEBCwUAA4IB\nAQBXvmyPWgXhC26cHYJBgQqj57dZ+n7p00kM1J+27oDMjGmbmX+XIKXLWazw/rG3\ngDjw9MXI2tVCrQMX0ohjphaULXhb/VBUPDOiW+k7C6AB3nZySFRflcR3cM4f83zF\nMoBd0549h5Red4p72FeOKNJRTN8YO4ooH9YNh5g0FQkgqn7fV9w2CNlomeKIW9zP\nm8tjFw0cJUk2wEYBVl8O7ko5rgNlzhkLoZkMvJhKa99AQJA6MAdyoLl1lv56Kq4X\njk+mMEiz9SaInp+ILQ1uQxZEwuC7DoGRW76rV4Fnie6+DLft4WKZfX1497mx8NV3\noR0abutJaKnCj07dwRu4/EsK\n-----END CERTIFICATE-----",
            "attr_first_name": "first_name",
        }
    },
    "SOCIAL_AUTH_SAML_CALLBACK_URL": "CALLBACK_URL",
}


@override_settings(**settings_dict)
class TestDumpAuthConfigCommand(TestCase):
    def setUp(self):
        super().setUp()
        self.expected_config = [
            {
                "type": "ansible_base.authentication.authenticator_plugins.saml",
                "name": "Keycloak",
                "enabled": True,
                "create_objects": True,
                "users_unique": False,
                "remove_users": True,
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
                    "ENABLED_IDPS": {
                        "Keycloak": {
                            "attr_last_name": "last_name",
                            "attr_groups": "groups",
                            "attr_email": "email",
                            "attr_user_permanent_id": "name_id",
                            "attr_username": "username",
                            "entity_id": "https://example.com/auth/realms/awx",
                            "url": "https://example.com/auth/realms/awx/protocol/saml",
                            "x509cert": "-----BEGIN CERTIFICATE-----\nMIIDDjCCAfYCCQCPBeVvpo8+VzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJV\nUzELMAkGA1UECAwCTkMxDzANBgNVBAcMBkR1cmhhbTEMMAoGA1UECgwDYXd4MQ4w\nDAYDVQQDDAVsb2NhbDAeFw0yNDAxMTgxNDA4MzFaFw0yNTAxMTcxNDA4MzFaMEkx\nCzAJBgNVBAYTAlVTMQswCQYDVQQIDAJOQzEPMA0GA1UEBwwGRHVyaGFtMQwwCgYD\nVQQKDANhd3gxDjAMBgNVBAMMBWxvY2FsMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A\nMIIBCgKCAQEAzouj93oyFXsHEABdPESh3CYpp5QJJBM4TLYIIolk6PFOFIVwBuFY\nfExi5w7Hh4A42lPM6RkrT+u3h7LV39H9MRUfqygOSmaxICTOI0sU9ROHc44fWWzN\n756OP4B5zSiqG82q8X7nYVkcID+2F/3ekPLMOlWn53OrcdfKKDIcqavoTkQJefc2\nggXU3WgVCxGki/qCm+e5cZ1Cpl/ykSLOT8dWMEzDd12kin66zJ3KYz9F2Q5kQTh4\nKRAChnBBoEqzOfENHEAaHALiXOlVSy61VcLbtvskRMMwBtsydlnd9n/HGnktgrid\n3Ca0z5wBTHWjAOBvCKxKJuDa+jmyHEnpcQIDAQABMA0GCSqGSIb3DQEBCwUAA4IB\nAQBXvmyPWgXhC26cHYJBgQqj57dZ+n7p00kM1J+27oDMjGmbmX+XIKXLWazw/rG3\ngDjw9MXI2tVCrQMX0ohjphaULXhb/VBUPDOiW+k7C6AB3nZySFRflcR3cM4f83zF\nMoBd0549h5Red4p72FeOKNJRTN8YO4ooH9YNh5g0FQkgqn7fV9w2CNlomeKIW9zP\nm8tjFw0cJUk2wEYBVl8O7ko5rgNlzhkLoZkMvJhKa99AQJA6MAdyoLl1lv56Kq4X\njk+mMEiz9SaInp+ILQ1uQxZEwuC7DoGRW76rV4Fnie6+DLft4WKZfX1497mx8NV3\noR0abutJaKnCj07dwRu4/EsK\n-----END CERTIFICATE-----",
                            "attr_first_name": "first_name",
                        }
                    },
                    "CALLBACK_URL": "CALLBACK_URL",
                    "IDP_URL": "https://example.com/auth/realms/awx/protocol/saml",
                    "IDP_X509_CERT": "-----BEGIN CERTIFICATE-----\nMIIDDjCCAfYCCQCPBeVvpo8+VzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJV\nUzELMAkGA1UECAwCTkMxDzANBgNVBAcMBkR1cmhhbTEMMAoGA1UECgwDYXd4MQ4w\nDAYDVQQDDAVsb2NhbDAeFw0yNDAxMTgxNDA4MzFaFw0yNTAxMTcxNDA4MzFaMEkx\nCzAJBgNVBAYTAlVTMQswCQYDVQQIDAJOQzEPMA0GA1UEBwwGRHVyaGFtMQwwCgYD\nVQQKDANhd3gxDjAMBgNVBAMMBWxvY2FsMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A\nMIIBCgKCAQEAzouj93oyFXsHEABdPESh3CYpp5QJJBM4TLYIIolk6PFOFIVwBuFY\nfExi5w7Hh4A42lPM6RkrT+u3h7LV39H9MRUfqygOSmaxICTOI0sU9ROHc44fWWzN\n756OP4B5zSiqG82q8X7nYVkcID+2F/3ekPLMOlWn53OrcdfKKDIcqavoTkQJefc2\nggXU3WgVCxGki/qCm+e5cZ1Cpl/ykSLOT8dWMEzDd12kin66zJ3KYz9F2Q5kQTh4\nKRAChnBBoEqzOfENHEAaHALiXOlVSy61VcLbtvskRMMwBtsydlnd9n/HGnktgrid\n3Ca0z5wBTHWjAOBvCKxKJuDa+jmyHEnpcQIDAQABMA0GCSqGSIb3DQEBCwUAA4IB\nAQBXvmyPWgXhC26cHYJBgQqj57dZ+n7p00kM1J+27oDMjGmbmX+XIKXLWazw/rG3\ngDjw9MXI2tVCrQMX0ohjphaULXhb/VBUPDOiW+k7C6AB3nZySFRflcR3cM4f83zF\nMoBd0549h5Red4p72FeOKNJRTN8YO4ooH9YNh5g0FQkgqn7fV9w2CNlomeKIW9zP\nm8tjFw0cJUk2wEYBVl8O7ko5rgNlzhkLoZkMvJhKa99AQJA6MAdyoLl1lv56Kq4X\njk+mMEiz9SaInp+ILQ1uQxZEwuC7DoGRW76rV4Fnie6+DLft4WKZfX1497mx8NV3\noR0abutJaKnCj07dwRu4/EsK\n-----END CERTIFICATE-----",
                    "IDP_ENTITY_ID": "https://example.com/auth/realms/awx",
                    "IDP_ATTR_EMAIL": "email",
                    "IDP_GROUPS": "groups",
                    "IDP_ATTR_USERNAME": "username",
                    "IDP_ATTR_LAST_NAME": "last_name",
                    "IDP_ATTR_FIRST_NAME": "first_name",
                    "IDP_ATTR_USER_PERMANENT_ID": "name_id",
                },
            },
        ]

    def test_json_returned_from_cmd(self):
        output = StringIO()
        call_command("dump_auth_config", stdout=output)
        cmmd_output = json.loads(output.getvalue())

        # check configured SAML return
        assert cmmd_output[0] == self.expected_config[0]
