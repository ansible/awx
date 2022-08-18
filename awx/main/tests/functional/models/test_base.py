from unittest import mock
import pytest

from crum import impersonate

from awx.main.models import Host


@pytest.mark.django_db
def test_modified_by_not_changed(inventory):
    with impersonate(None):
        host = Host.objects.create(name='foo', inventory=inventory)
        assert host.modified_by == None
        host.variables = {'foo': 'bar'}
        with mock.patch('django.db.models.Model.save') as save_mock:
            host.save(update_fields=['variables'])
            save_mock.assert_called_once_with(update_fields=['variables'])


@pytest.mark.django_db
def test_modified_by_changed(inventory, alice):
    with impersonate(None):
        host = Host.objects.create(name='foo', inventory=inventory)
        assert host.modified_by == None
    with impersonate(alice):
        host.variables = {'foo': 'bar'}
        with mock.patch('django.db.models.Model.save') as save_mock:
            host.save(update_fields=['variables'])
            save_mock.assert_called_once_with(update_fields=['variables', 'modified_by'])
        assert host.modified_by == alice


@pytest.mark.django_db
def test_created_by(inventory, alice):
    with impersonate(alice):
        host = Host.objects.create(name='foo', inventory=inventory)
        assert host.created_by == alice
    with impersonate(None):
        host = Host.objects.create(name='bar', inventory=inventory)
        assert host.created_by == None
