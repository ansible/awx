import pytest
import yaml
from unittest import mock

from awx.api.versioning import reverse
from awx.main.models import Instance, ReceptorAddress
from awx.api.views.instance_install_bundle import generate_group_vars_all_yml


def has_peer(group_vars, peer):
    peers = group_vars.get('receptor_peers', [])
    for p in peers:
        if p['address'] == peer:
            return True
    return False


@pytest.mark.django_db
class TestPeers:
    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        settings.IS_K8S = True

    @pytest.mark.parametrize('node_type', ['hop', 'execution'])
    def test_peering_to_self(self, node_type, admin_user, patch):
        """
        cannot peer to self
        """
        instance = Instance.objects.create(hostname='abc', node_type=node_type)
        addr = ReceptorAddress.objects.create(instance=instance, address='abc', canonical=True)
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': instance.pk}),
            data={"hostname": "abc", "node_type": node_type, "peers": [addr.id]},
            user=admin_user,
            expect=400,
        )
        assert 'Instance cannot peer to its own address.' in str(resp.data)

    @pytest.mark.parametrize('node_type', ['control', 'hybrid', 'hop', 'execution'])
    def test_creating_node(self, node_type, admin_user, post):
        """
        can only add hop and execution nodes via API
        """
        resp = post(
            url=reverse('api:instance_list'),
            data={"hostname": "abc", "node_type": node_type},
            user=admin_user,
            expect=400 if node_type in ['control', 'hybrid'] else 201,
        )
        if resp.status_code == 400:
            assert 'Can only create execution or hop nodes.' in str(resp.data)

    def test_changing_node_type(self, admin_user, patch):
        """
        cannot change node type
        """
        hop = Instance.objects.create(hostname='abc', node_type="hop")
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"node_type": "execution"},
            user=admin_user,
            expect=400,
        )
        assert 'Cannot change node type.' in str(resp.data)

    @pytest.mark.parametrize(
        'payload_port, payload_peers_from, initial_port, initial_peers_from',
        [
            (-1, -1, None, None),
            (-1, -1, 27199, False),
            (-1, -1, 27199, True),
            (None, -1, None, None),
            (None, False, None, None),
            (-1, False, None, None),
            (27199, True, 27199, True),
            (27199, False, 27199, False),
            (27199, -1, 27199, True),
            (27199, -1, 27199, False),
            (-1, True, 27199, True),
            (-1, False, 27199, False),
        ],
    )
    def test_no_op(self, payload_port, payload_peers_from, initial_port, initial_peers_from, admin_user, patch):
        node = Instance.objects.create(hostname='abc', node_type='hop')
        if initial_port is not None:
            ReceptorAddress.objects.create(address=node.hostname, port=initial_port, canonical=True, peers_from_control_nodes=initial_peers_from, instance=node)

            assert ReceptorAddress.objects.filter(instance=node).count() == 1
        else:
            assert ReceptorAddress.objects.filter(instance=node).count() == 0

        data = {'enabled': True}  # Just to have something to post.
        if payload_port != -1:
            data['listener_port'] = payload_port
        if payload_peers_from != -1:
            data['peers_from_control_nodes'] = payload_peers_from

        patch(
            url=reverse('api:instance_detail', kwargs={'pk': node.pk}),
            data=data,
            user=admin_user,
            expect=200,
        )

        assert ReceptorAddress.objects.filter(instance=node).count() == (0 if initial_port is None else 1)
        if initial_port is not None:
            ra = ReceptorAddress.objects.get(instance=node, canonical=True)
            assert ra.port == initial_port
            assert ra.peers_from_control_nodes == initial_peers_from

    @pytest.mark.parametrize(
        'payload_port, payload_peers_from',
        [
            (27199, True),
            (27199, False),
            (27199, -1),
        ],
    )
    def test_creates_canonical_address(self, payload_port, payload_peers_from, admin_user, patch):
        node = Instance.objects.create(hostname='abc', node_type='hop')
        assert ReceptorAddress.objects.filter(instance=node).count() == 0

        data = {'enabled': True}  # Just to have something to post.
        if payload_port != -1:
            data['listener_port'] = payload_port
        if payload_peers_from != -1:
            data['peers_from_control_nodes'] = payload_peers_from

        patch(
            url=reverse('api:instance_detail', kwargs={'pk': node.pk}),
            data=data,
            user=admin_user,
            expect=200,
        )

        assert ReceptorAddress.objects.filter(instance=node).count() == 1
        ra = ReceptorAddress.objects.get(instance=node, canonical=True)
        assert ra.port == payload_port
        assert ra.peers_from_control_nodes == (payload_peers_from if payload_peers_from != -1 else False)

    @pytest.mark.parametrize(
        'payload_port, payload_peers_from, initial_port, initial_peers_from',
        [
            (None, False, 27199, True),
            (None, -1, 27199, True),
            (None, False, 27199, False),
            (None, -1, 27199, False),
        ],
    )
    def test_deletes_canonical_address(self, payload_port, payload_peers_from, initial_port, initial_peers_from, admin_user, patch):
        node = Instance.objects.create(hostname='abc', node_type='hop')
        ReceptorAddress.objects.create(address=node.hostname, port=initial_port, canonical=True, peers_from_control_nodes=initial_peers_from, instance=node)

        assert ReceptorAddress.objects.filter(instance=node).count() == 1

        data = {'enabled': True}  # Just to have something to post.
        if payload_port != -1:
            data['listener_port'] = payload_port
        if payload_peers_from != -1:
            data['peers_from_control_nodes'] = payload_peers_from

        patch(
            url=reverse('api:instance_detail', kwargs={'pk': node.pk}),
            data=data,
            user=admin_user,
            expect=200,
        )

        assert ReceptorAddress.objects.filter(instance=node).count() == 0

    @pytest.mark.parametrize(
        'payload_port, payload_peers_from, initial_port, initial_peers_from',
        [
            (27199, True, 27199, False),
            (27199, False, 27199, True),
            (-1, True, 27199, False),
            (-1, False, 27199, True),
        ],
    )
    def test_updates_canonical_address(self, payload_port, payload_peers_from, initial_port, initial_peers_from, admin_user, patch):
        node = Instance.objects.create(hostname='abc', node_type='hop')
        ReceptorAddress.objects.create(address=node.hostname, port=initial_port, canonical=True, peers_from_control_nodes=initial_peers_from, instance=node)

        assert ReceptorAddress.objects.filter(instance=node).count() == 1

        data = {'enabled': True}  # Just to have something to post.
        if payload_port != -1:
            data['listener_port'] = payload_port
        if payload_peers_from != -1:
            data['peers_from_control_nodes'] = payload_peers_from

        patch(
            url=reverse('api:instance_detail', kwargs={'pk': node.pk}),
            data=data,
            user=admin_user,
            expect=200,
        )

        assert ReceptorAddress.objects.filter(instance=node).count() == 1
        ra = ReceptorAddress.objects.get(instance=node, canonical=True)
        assert ra.port == initial_port  # At the present time, changing ports is not allowed
        assert ra.peers_from_control_nodes == payload_peers_from

    @pytest.mark.parametrize(
        'payload_port, payload_peers_from, initial_port, initial_peers_from, error_msg',
        [
            (-1, True, None, None, "Cannot enable peers_from_control_nodes"),
            (None, True, None, None, "Cannot enable peers_from_control_nodes"),
            (None, True, 21799, True, "Cannot enable peers_from_control_nodes"),
            (None, True, 21799, False, "Cannot enable peers_from_control_nodes"),
            (21800, -1, 21799, True, "Cannot change listener port"),
            (21800, True, 21799, True, "Cannot change listener port"),
            (21800, False, 21799, True, "Cannot change listener port"),
            (21800, -1, 21799, False, "Cannot change listener port"),
            (21800, True, 21799, False, "Cannot change listener port"),
            (21800, False, 21799, False, "Cannot change listener port"),
        ],
    )
    def test_canonical_address_validation_error(self, payload_port, payload_peers_from, initial_port, initial_peers_from, error_msg, admin_user, patch):
        node = Instance.objects.create(hostname='abc', node_type='hop')
        if initial_port is not None:
            ReceptorAddress.objects.create(address=node.hostname, port=initial_port, canonical=True, peers_from_control_nodes=initial_peers_from, instance=node)

            assert ReceptorAddress.objects.filter(instance=node).count() == 1
        else:
            assert ReceptorAddress.objects.filter(instance=node).count() == 0

        data = {'enabled': True}  # Just to have something to post.
        if payload_port != -1:
            data['listener_port'] = payload_port
        if payload_peers_from != -1:
            data['peers_from_control_nodes'] = payload_peers_from

        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': node.pk}),
            data=data,
            user=admin_user,
            expect=400,
        )

        assert error_msg in str(resp.data)

    def test_changing_managed_listener_port(self, admin_user, patch):
        """
        if instance is managed, cannot change listener port at all
        """
        hop = Instance.objects.create(hostname='abc', node_type="hop", managed=True)
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"listener_port": 5678},
            user=admin_user,
            expect=400,  # cannot set port
        )
        assert 'Cannot change listener port for managed nodes.' in str(resp.data)
        ReceptorAddress.objects.create(instance=hop, address='hop', port=27199, canonical=True)
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"listener_port": None},
            user=admin_user,
            expect=400,  # cannot unset port
        )
        assert 'Cannot change listener port for managed nodes.' in str(resp.data)

    def test_bidirectional_peering(self, admin_user, patch):
        """
        cannot peer to node that is already to peered to it
        if A -> B, then disallow B -> A
        """
        hop1 = Instance.objects.create(hostname='hop1', node_type='hop')
        hop1addr = ReceptorAddress.objects.create(instance=hop1, address='hop1', canonical=True)
        hop2 = Instance.objects.create(hostname='hop2', node_type='hop')
        hop2addr = ReceptorAddress.objects.create(instance=hop2, address='hop2', canonical=True)
        hop1.peers.add(hop2addr)
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop2.pk}),
            data={"peers": [hop1addr.id]},
            user=admin_user,
            expect=400,
        )
        assert 'Instance hop1 is already peered to this instance.' in str(resp.data)

    def test_multiple_peers_same_instance(self, admin_user, patch):
        """
        cannot peer to more than one address of the same instance
        """
        hop1 = Instance.objects.create(hostname='hop1', node_type='hop')
        hop1addr1 = ReceptorAddress.objects.create(instance=hop1, address='hop1', canonical=True)
        hop1addr2 = ReceptorAddress.objects.create(instance=hop1, address='hop1alternate')
        hop2 = Instance.objects.create(hostname='hop2', node_type='hop')
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop2.pk}),
            data={"peers": [hop1addr1.id, hop1addr2.id]},
            user=admin_user,
            expect=400,
        )
        assert 'Cannot peer to the same instance more than once.' in str(resp.data)

    @pytest.mark.parametrize('node_type', ['control', 'hybrid'])
    def test_changing_peers_control_nodes(self, node_type, admin_user, patch):
        """
        for control nodes, peers field should not be
        modified directly via patch.
        """
        control = Instance.objects.create(hostname='abc', node_type=node_type, managed=True)
        hop1 = Instance.objects.create(hostname='hop1', node_type='hop')
        hop1addr = ReceptorAddress.objects.create(instance=hop1, address='hop1', peers_from_control_nodes=True, canonical=True)
        hop2 = Instance.objects.create(hostname='hop2', node_type='hop')
        hop2addr = ReceptorAddress.objects.create(instance=hop2, address='hop2', canonical=True)
        assert [hop1addr] == list(control.peers.all())  # only hop1addr should be peered
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': control.pk}),
            data={"peers": [hop2addr.id]},
            user=admin_user,
            expect=400,  # cannot add peers manually
        )
        assert 'Setting peers manually for managed nodes is not allowed.' in str(resp.data)

        patch(
            url=reverse('api:instance_detail', kwargs={'pk': control.pk}),
            data={"peers": [hop1addr.id]},
            user=admin_user,
            expect=200,  # patching with current peers list should be okay
        )
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': control.pk}),
            data={"peers": []},
            user=admin_user,
            expect=400,  # cannot remove peers directly
        )
        assert 'Setting peers manually for managed nodes is not allowed.' in str(resp.data)

        patch(
            url=reverse('api:instance_detail', kwargs={'pk': control.pk}),
            data={},
            user=admin_user,
            expect=200,  # patching without data should be fine too
        )
        # patch hop2
        patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop2.pk}),
            data={"peers_from_control_nodes": True},
            user=admin_user,
            expect=200,
        )
        assert {hop1addr, hop2addr} == set(control.peers.all())  # hop1 and hop2 should now be peered from control node

    def test_changing_hostname(self, admin_user, patch):
        """
        cannot change hostname
        """
        hop = Instance.objects.create(hostname='hop', node_type='hop')
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"hostname": "hop2"},
            user=admin_user,
            expect=400,
        )

        assert 'Cannot change hostname.' in str(resp.data)

    def test_changing_node_state(self, admin_user, patch):
        """
        only allow setting to deprovisioning
        """
        hop = Instance.objects.create(hostname='hop', node_type='hop', node_state='installed')
        patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"node_state": "deprovisioning"},
            user=admin_user,
            expect=200,
        )
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"node_state": "ready"},
            user=admin_user,
            expect=400,
        )
        assert "Can only change instances to the 'deprovisioning' state." in str(resp.data)

    def test_changing_managed_node_state(self, admin_user, patch):
        """
        cannot change node state of managed node
        """
        hop = Instance.objects.create(hostname='hop', node_type='hop', managed=True)
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"node_state": "deprovisioning"},
            user=admin_user,
            expect=400,
        )

        assert 'Cannot deprovision managed nodes.' in str(resp.data)

    def test_changing_managed_peers_from_control_nodes(self, admin_user, patch):
        """
        cannot change peers_from_control_nodes of managed node
        """
        hop = Instance.objects.create(hostname='hop', node_type='hop', managed=True)
        ReceptorAddress.objects.create(instance=hop, address='hop', peers_from_control_nodes=True, canonical=True)
        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"peers_from_control_nodes": False},
            user=admin_user,
            expect=400,
        )

        assert 'Cannot change peers_from_control_nodes for managed nodes.' in str(resp.data)

        hop.peers_from_control_nodes = False
        hop.save()

        resp = patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"peers_from_control_nodes": False},
            user=admin_user,
            expect=400,
        )

        assert 'Cannot change peers_from_control_nodes for managed nodes.' in str(resp.data)

    @pytest.mark.parametrize('node_type', ['control', 'hybrid'])
    def test_control_node_automatically_peers(self, node_type):
        """
        a new control node should automatically
        peer to hop

        peer to hop should be removed if hop is deleted
        """

        hop = Instance.objects.create(hostname='hop', node_type='hop')
        hopaddr = ReceptorAddress.objects.create(instance=hop, address='hop', peers_from_control_nodes=True, canonical=True)
        control = Instance.objects.create(hostname='abc', node_type=node_type)
        assert hopaddr in control.peers.all()
        hop.delete()
        assert not control.peers.exists()

    @pytest.mark.parametrize('node_type', ['control', 'hybrid'])
    def test_control_node_retains_other_peers(self, node_type):
        """
        if a new node comes online, other peer relationships should
        remain intact
        """
        hop1 = Instance.objects.create(hostname='hop1', node_type='hop')
        hop2 = Instance.objects.create(hostname='hop2', node_type='hop')
        hop2addr = ReceptorAddress.objects.create(instance=hop2, address='hop2', canonical=True)
        hop1.peers.add(hop2addr)

        # a control node is added
        Instance.objects.create(hostname='control', node_type=node_type)

        assert hop1.peers.exists()

    def test_reverse_peers(self, admin_user, get):
        """
        if hop1 peers to hop2, hop1 should
        be in hop2's reverse_peers list
        """
        hop1 = Instance.objects.create(hostname='hop1', node_type='hop')
        hop2 = Instance.objects.create(hostname='hop2', node_type='hop')
        hop2addr = ReceptorAddress.objects.create(instance=hop2, address='hop2', canonical=True)
        hop1.peers.add(hop2addr)

        resp = get(
            url=reverse('api:instance_detail', kwargs={'pk': hop2.pk}),
            user=admin_user,
            expect=200,
        )

        assert hop1.pk in resp.data['reverse_peers']

    def test_group_vars(self):
        """
        control > hop1 > hop2 < execution
        """
        control = Instance.objects.create(hostname='control', node_type='control')
        hop1 = Instance.objects.create(hostname='hop1', node_type='hop')
        ReceptorAddress.objects.create(instance=hop1, address='hop1', peers_from_control_nodes=True, port=6789, canonical=True)

        hop2 = Instance.objects.create(hostname='hop2', node_type='hop')
        hop2addr = ReceptorAddress.objects.create(instance=hop2, address='hop2', peers_from_control_nodes=False, port=6789, canonical=True)

        execution = Instance.objects.create(hostname='execution', node_type='execution')
        ReceptorAddress.objects.create(instance=execution, address='execution', peers_from_control_nodes=False, port=6789, canonical=True)

        execution.peers.add(hop2addr)
        hop1.peers.add(hop2addr)

        control_vars = yaml.safe_load(generate_group_vars_all_yml(control))
        hop1_vars = yaml.safe_load(generate_group_vars_all_yml(hop1))
        hop2_vars = yaml.safe_load(generate_group_vars_all_yml(hop2))
        execution_vars = yaml.safe_load(generate_group_vars_all_yml(execution))

        # control group vars assertions
        assert has_peer(control_vars, 'hop1:6789')
        assert not has_peer(control_vars, 'hop2:6789')
        assert not has_peer(control_vars, 'execution:6789')
        assert not control_vars.get('receptor_listener', False)

        # hop1 group vars assertions
        assert has_peer(hop1_vars, 'hop2:6789')
        assert not has_peer(hop1_vars, 'execution:6789')
        assert hop1_vars.get('receptor_listener', False)

        # hop2 group vars assertions
        assert not has_peer(hop2_vars, 'hop1:6789')
        assert not has_peer(hop2_vars, 'execution:6789')
        assert hop2_vars.get('receptor_listener', False)
        assert hop2_vars.get('receptor_peers', []) == []

        # execution group vars assertions
        assert has_peer(execution_vars, 'hop2:6789')
        assert not has_peer(execution_vars, 'hop1:6789')
        assert execution_vars.get('receptor_listener', False)

    def test_write_receptor_config_called(self):
        """
        Assert that write_receptor_config is called
        when certain instances are created, or if
        peers_from_control_nodes changes.
        In general, write_receptor_config should only
        be called when necessary, as it will reload
        receptor backend connections which is not trivial.
        """
        with mock.patch('awx.main.models.ha.schedule_write_receptor_config') as write_method:
            # new control instance but nothing to peer to (no)
            control = Instance.objects.create(hostname='control1', node_type='control')
            write_method.assert_not_called()

            # new address with peers_from_control_nodes False (no)
            hop1 = Instance.objects.create(hostname='hop1', node_type='hop')
            hop1addr = ReceptorAddress.objects.create(instance=hop1, address='hop1', peers_from_control_nodes=False, canonical=True)
            hop1.delete()
            write_method.assert_not_called()

            # new address with peers_from_control_nodes True (yes)
            hop1 = Instance.objects.create(hostname='hop1', node_type='hop')
            hop1addr = ReceptorAddress.objects.create(instance=hop1, address='hop1', peers_from_control_nodes=True, canonical=True)
            write_method.assert_called()
            write_method.reset_mock()

            # new control instance but with something to peer to (yes)
            Instance.objects.create(hostname='control2', node_type='control')
            write_method.assert_called()
            write_method.reset_mock()

            # new address with peers_from_control_nodes False and peered to another hop node (no)
            hop2 = Instance.objects.create(hostname='hop2', node_type='hop')
            ReceptorAddress.objects.create(instance=hop2, address='hop2', peers_from_control_nodes=False, canonical=True)
            hop2.peers.add(hop1addr)
            hop2.delete()
            write_method.assert_not_called()

            # changing peers_from_control_nodes to False (yes)
            hop1addr.peers_from_control_nodes = False
            hop1addr.save()
            write_method.assert_called()
            write_method.reset_mock()

            # deleting address that has peers_from_control_nodes to False (no)
            hop1.delete()  # cascade deletes to hop1addr
            write_method.assert_not_called()

            # deleting control nodes (no)
            control.delete()
            write_method.assert_not_called()

    def test_write_receptor_config_data(self):
        """
        Assert the correct peers are included in data that will
        be written to receptor.conf
        """
        from awx.main.tasks.receptor import RECEPTOR_CONFIG_STARTER

        with mock.patch('awx.main.tasks.receptor.read_receptor_config', return_value=list(RECEPTOR_CONFIG_STARTER)):
            from awx.main.tasks.receptor import generate_config_data

            _, should_update = generate_config_data()
            assert not should_update

            # not peered, so config file should not be updated
            for i in range(3):
                inst = Instance.objects.create(hostname=f"exNo-{i}", node_type='execution')
                ReceptorAddress.objects.create(instance=inst, address=f"exNo-{i}", port=6789, peers_from_control_nodes=False, canonical=True)
            _, should_update = generate_config_data()
            assert not should_update

            # peered, so config file should be updated
            expected_peers = []
            for i in range(3):
                expected_peers.append(f"hop-{i}:6789")
                inst = Instance.objects.create(hostname=f"hop-{i}", node_type='hop')
                ReceptorAddress.objects.create(instance=inst, address=f"hop-{i}", port=6789, peers_from_control_nodes=True, canonical=True)

            for i in range(3):
                expected_peers.append(f"exYes-{i}:6789")
                inst = Instance.objects.create(hostname=f"exYes-{i}", node_type='execution')
                ReceptorAddress.objects.create(instance=inst, address=f"exYes-{i}", port=6789, peers_from_control_nodes=True, canonical=True)

            new_config, should_update = generate_config_data()
            assert should_update

            peers = []
            for entry in new_config:
                for key, value in entry.items():
                    if key == "tcp-peer":
                        peers.append(value['address'])

            assert set(expected_peers) == set(peers)
