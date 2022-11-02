import pytest

from awx.main.management.commands.provision_instance import Command
from awx.main.models.ha import InstanceGroup, Instance
from awx.main.tasks.system import apply_cluster_membership_policies

from django.test.utils import override_settings


@pytest.mark.django_db
def test_traditional_registration():
    assert not Instance.objects.exists()
    assert not InstanceGroup.objects.exists()

    Command().handle(hostname='bar_node', node_type='execution', uuid='4321')

    inst = Instance.objects.first()
    assert inst.hostname == 'bar_node'
    assert inst.node_type == 'execution'
    assert inst.uuid == '4321'

    assert not InstanceGroup.objects.exists()


@pytest.mark.django_db
def test_register_self_openshift():
    assert not Instance.objects.exists()
    assert not InstanceGroup.objects.exists()

    with override_settings(AWX_AUTO_DEPROVISION_INSTANCES=True, CLUSTER_HOST_ID='foo_node', SYSTEM_UUID='12345'):
        Command().handle()
    inst = Instance.objects.first()
    assert inst.hostname == 'foo_node'
    assert inst.uuid == '12345'
    assert inst.node_type == 'control'

    apply_cluster_membership_policies()  # populate instance list using policy rules

    assert list(InstanceGroup.objects.get(name='default').instances.all()) == []  # container group
    assert list(InstanceGroup.objects.get(name='controlplane').instances.all()) == [inst]
