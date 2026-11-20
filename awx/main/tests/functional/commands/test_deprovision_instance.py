import pytest
from django.core.management.base import CommandError

from awx.main.management.commands.deprovision_instance import Command
from awx.main.models.ha import Instance


@pytest.mark.django_db
def test_deprovision_instance_requires_hostname():
    with pytest.raises(CommandError, match='--hostname is a required argument'):
        Command().handle(hostname=None)


@pytest.mark.django_db
def test_deprovision_instance_skips_empty_hostname():
    assert not Instance.objects.filter(hostname='').exists()
    # Should not raise; installers may pass --hostname= (AAP-75757)
    Command().handle(hostname='')
    Command().handle(hostname='   ')
    assert not Instance.objects.filter(hostname='').exists()


@pytest.mark.django_db
def test_deprovision_instance_removes_matching_hostname():
    Instance.objects.create(hostname='gone.example.com', node_type='execution', uuid='11111111-1111-1111-1111-111111111111')
    Command().handle(hostname='gone.example.com')
    assert not Instance.objects.filter(hostname='gone.example.com').exists()
