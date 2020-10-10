import importlib

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
import pytest

from awx.main.models import Credential, Organization
from awx.conf.models import Setting
from awx.main.migrations import _galaxy as galaxy


class FakeApps(object):
    def get_model(self, app, model):
        if app == 'contenttypes':
            return ContentType
        return getattr(importlib.import_module(f'awx.{app}.models'), model)


apps = FakeApps()


@pytest.mark.django_db
def test_default_public_galaxy():
    org = Organization.objects.create()
    assert org.galaxy_credentials.count() == 0
    galaxy.migrate_galaxy_settings(apps, None)
    assert org.galaxy_credentials.count() == 1
    creds = org.galaxy_credentials.all()
    assert creds[0].name == 'Ansible Galaxy'
    assert creds[0].inputs['url'] == 'https://galaxy.ansible.com/'


@pytest.mark.django_db
def test_public_galaxy_disabled():
    Setting.objects.create(key='PUBLIC_GALAXY_ENABLED', value=False)
    org = Organization.objects.create()
    assert org.galaxy_credentials.count() == 0
    galaxy.migrate_galaxy_settings(apps, None)
    assert org.galaxy_credentials.count() == 0


@pytest.mark.django_db
def test_rh_automation_hub():
    Setting.objects.create(key='PRIMARY_GALAXY_URL', value='https://cloud.redhat.com/api/automation-hub/')
    Setting.objects.create(key='PRIMARY_GALAXY_TOKEN', value='secret123')
    org = Organization.objects.create()
    assert org.galaxy_credentials.count() == 0
    galaxy.migrate_galaxy_settings(apps, None)
    assert org.galaxy_credentials.count() == 2
    assert org.galaxy_credentials.first().name == 'Ansible Automation Hub (https://cloud.redhat.com/api/automation-hub/)'  # noqa


@pytest.mark.django_db
def test_multiple_galaxies():
    for i in range(5):
        Organization.objects.create(name=f'Org {i}')

    Setting.objects.create(key='PRIMARY_GALAXY_URL', value='https://example.org/')
    Setting.objects.create(key='PRIMARY_GALAXY_AUTH_URL', value='https://auth.example.org/')
    Setting.objects.create(key='PRIMARY_GALAXY_USERNAME', value='user')
    Setting.objects.create(key='PRIMARY_GALAXY_PASSWORD', value='pass')
    Setting.objects.create(key='PRIMARY_GALAXY_TOKEN', value='secret123')

    for org in Organization.objects.all():
        assert org.galaxy_credentials.count() == 0

    galaxy.migrate_galaxy_settings(apps, None)

    for org in Organization.objects.all():
        assert org.galaxy_credentials.count() == 2
        creds = org.galaxy_credentials.all()
        assert creds[0].name == 'Private Galaxy (https://example.org/)'
        assert creds[0].inputs['url'] == 'https://example.org/'
        assert creds[0].inputs['auth_url'] == 'https://auth.example.org/'
        assert creds[0].inputs['token'].startswith('$encrypted$')
        assert creds[0].get_input('token') == 'secret123'

        assert creds[1].name == 'Ansible Galaxy'
        assert creds[1].inputs['url'] == 'https://galaxy.ansible.com/'

    public_galaxy_creds = Credential.objects.filter(name='Ansible Galaxy')
    assert public_galaxy_creds.count() == 1
    assert public_galaxy_creds.first().managed_by_tower is True


@pytest.mark.django_db
def test_fallback_galaxies():
    org = Organization.objects.create()
    assert org.galaxy_credentials.count() == 0
    Setting.objects.create(key='PRIMARY_GALAXY_URL', value='https://example.org/')
    Setting.objects.create(key='PRIMARY_GALAXY_AUTH_URL', value='https://auth.example.org/')
    Setting.objects.create(key='PRIMARY_GALAXY_TOKEN', value='secret123')
    try:
        settings.FALLBACK_GALAXY_SERVERS = [{
            'id': 'abc123',
            'url': 'https://some-other-galaxy.example.org/',
            'auth_url': 'https://some-other-galaxy.sso.example.org/',
            'username': 'user',
            'password': 'pass',
            'token': 'fallback123',
        }]
        galaxy.migrate_galaxy_settings(apps, None)
    finally:
        settings.FALLBACK_GALAXY_SERVERS = []
    assert org.galaxy_credentials.count() == 3
    creds = org.galaxy_credentials.all()
    assert creds[0].name == 'Private Galaxy (https://example.org/)'
    assert creds[0].inputs['url'] == 'https://example.org/'
    assert creds[1].name == 'Ansible Galaxy (https://some-other-galaxy.example.org/)'
    assert creds[1].inputs['url'] == 'https://some-other-galaxy.example.org/'
    assert creds[1].inputs['auth_url'] == 'https://some-other-galaxy.sso.example.org/'
    assert creds[1].inputs['token'].startswith('$encrypted$')
    assert creds[1].get_input('token') == 'fallback123'
    assert creds[2].name == 'Ansible Galaxy'
    assert creds[2].inputs['url'] == 'https://galaxy.ansible.com/'
