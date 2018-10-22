
import ldap
import ldif
import pytest
import os
from mockldap import MockLdap

from awx.api.versioning import reverse


@pytest.fixture
def ldap_generator():
    def fn(fname, host='localhost'):

        fh = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), fname), 'rb')
        ctrl = ldif.LDIFRecordList(fh)
        ctrl.parse()

        directory = dict(ctrl.all_records)

        mockldap = MockLdap(directory)

        mockldap.start()
        mockldap['ldap://{}/'.format(host)]

        conn = ldap.initialize('ldap://{}/'.format(host))

        return conn
        #mockldap.stop()

    return fn


@pytest.fixture
def ldap_settings_generator():
    def fn(prefix='', dc='ansible', host='ldap.ansible.com'):
        prefix = '_{}'.format(prefix) if prefix else ''

        data = {
            'AUTH_LDAP_SERVER_URI': 'ldap://{}'.format(host),
            'AUTH_LDAP_BIND_DN': 'cn=eng_user1,ou=people,dc={},dc=com'.format(dc),
            'AUTH_LDAP_BIND_PASSWORD': 'password',
            "AUTH_LDAP_USER_SEARCH": [
                "ou=people,dc={},dc=com".format(dc),
                "SCOPE_SUBTREE",
                "(cn=%(user)s)"
            ],
            "AUTH_LDAP_TEAM_MAP": {
                "LDAP Sales": {
                    "organization": "LDAP Organization",
                    "users": "cn=sales,ou=groups,dc={},dc=com".format(dc),
                    "remove": True
                },
                "LDAP IT": {
                    "organization": "LDAP Organization",
                    "users": "cn=it,ou=groups,dc={},dc=com".format(dc),
                    "remove": True
                },
                "LDAP Engineering": {
                    "organization": "LDAP Organization",
                    "users": "cn=engineering,ou=groups,dc={},dc=com".format(dc),
                    "remove": True
                }
            },
            "AUTH_LDAP_REQUIRE_GROUP": None,
            "AUTH_LDAP_USER_ATTR_MAP": {
                "first_name": "givenName",
                "last_name": "sn",
                "email": "mail"
            },
            "AUTH_LDAP_GROUP_SEARCH": [
                "dc={},dc=com".format(dc),
                "SCOPE_SUBTREE",
                "(objectClass=groupOfNames)"
            ],
            "AUTH_LDAP_USER_FLAGS_BY_GROUP": {
                "is_superuser": "cn=superusers,ou=groups,dc={},dc=com".format(dc)
            },
            "AUTH_LDAP_ORGANIZATION_MAP": {
                "LDAP Organization": {
                    "admins": "cn=engineering_admins,ou=groups,dc={},dc=com".format(dc),
                    "remove_admins": False,
                    "users": [
                        "cn=engineering,ou=groups,dc={},dc=com".format(dc),
                        "cn=sales,ou=groups,dc={},dc=com".format(dc),
                        "cn=it,ou=groups,dc={},dc=com".format(dc)
                    ],
                    "remove_users": False
                }
            },
        }

        if prefix:
            data_new = dict()
            for k,v in data.items():
                k_new = k.replace('AUTH_LDAP', 'AUTH_LDAP{}'.format(prefix))
                data_new[k_new] = v
        else:
            data_new = data

        return data_new
    return fn


# Note: mockldap isn't fully featured. Fancy queries aren't fully baked.
# However, objects returned are solid so they should flow through django ldap middleware nicely.
@pytest.mark.skip(reason="Needs Update - CA")
@pytest.mark.django_db
def test_login(ldap_generator, patch, post, admin, ldap_settings_generator):
    auth_url = reverse('api:auth_token_view')
    ldap_settings_url = reverse('api:setting_singleton_detail', kwargs={'category_slug': 'ldap'})

    # Generate mock ldap servers and init with ldap data
    ldap_generator("../data/ldap_example.ldif", "ldap.example.com")
    ldap_generator("../data/ldap_redhat.ldif", "ldap.redhat.com")
    ldap_generator("../data/ldap_ansible.ldif", "ldap.ansible.com")

    ldap_settings_example = ldap_settings_generator(dc='example')
    ldap_settings_ansible = ldap_settings_generator(prefix='1', dc='ansible')
    ldap_settings_redhat = ldap_settings_generator(prefix='2', dc='redhat')

    # eng_user1 exists in ansible and redhat but not example
    patch(ldap_settings_url, user=admin, data=ldap_settings_example, expect=200)

    post(auth_url, data={'username': 'eng_user1', 'password': 'password'}, expect=400)

    patch(ldap_settings_url, user=admin, data=ldap_settings_ansible, expect=200)
    patch(ldap_settings_url, user=admin, data=ldap_settings_redhat, expect=200)

    post(auth_url, data={'username': 'eng_user1', 'password': 'password'}, expect=200)

