import pytest

from awx.main.models import Instance, ReceptorAddress, InstanceLink
from awx.main.tasks.system import inspect_established_receptor_connections


@pytest.mark.django_db
class TestLinkState:
    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        settings.IS_K8S = True

    def test_inspect_established_receptor_connections(self):
        '''
        Change link state from ADDING to ESTABLISHED
        if the receptor status KnownConnectionCosts field
        has an entry for the source and target node.
        '''
        hop1 = Instance.objects.create(hostname='hop1')
        hop2 = Instance.objects.create(hostname='hop2')
        hop2addr = ReceptorAddress.objects.create(instance=hop2, address='hop2', port=5678)
        InstanceLink.objects.create(source=hop1, target=hop2addr, link_state=InstanceLink.States.ADDING)

        # calling with empty KnownConnectionCosts should not change the link state
        inspect_established_receptor_connections({"KnownConnectionCosts": {}})
        assert InstanceLink.objects.get(source=hop1, target=hop2addr).link_state == InstanceLink.States.ADDING

        mesh_state = {"KnownConnectionCosts": {"hop1": {"hop2": 1}}}
        inspect_established_receptor_connections(mesh_state)
        assert InstanceLink.objects.get(source=hop1, target=hop2addr).link_state == InstanceLink.States.ESTABLISHED
