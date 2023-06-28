import pytest
import yaml
from unittest import mock

from django.db.utils import IntegrityError

from awx.api.versioning import reverse
from awx.main.models import Instance
from awx.api.views.instance_install_bundle import generate_group_vars_all_yml


@pytest.mark.django_db
class TestPeers:
    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        settings.IS_K8S = True

    def test_prevent_peering_to_self(self):
        '''
        cannot peer to self
        '''
        control_instance = Instance.objects.create(hostname='abc', node_type="control")
        with pytest.raises(IntegrityError):
            control_instance.peers.add(control_instance)

    @pytest.mark.parametrize('node_type', ['control', 'hop', 'execution'])
    def test_creating_node(self, node_type, admin_user, post):
        '''
        can only add hop and execution nodes via API
        '''
        post(
            url=reverse('api:instance_list'),
            data={"hostname": "abc", "node_type": node_type},
            user=admin_user,
            expect=400 if node_type == 'control' else 201,
        )

    def test_changing_node_type(self, admin_user, patch):
        '''
        cannot change node type
        '''
        hop = Instance.objects.create(hostname='abc', node_type="hop")
        patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"node_type": "execution"},
            user=admin_user,
            expect=400,
        )

    @pytest.mark.parametrize('node_type', ['hop', 'execution'])
    def test_listener_port_null(self, node_type, admin_user, post):
        '''
        listener_port can be None
        '''
        post(
            url=reverse('api:instance_list'),
            data={"hostname": "abc", "node_type": node_type, "listener_port": None},
            user=admin_user,
            expect=201,
        )

    @pytest.mark.parametrize('node_type, allowed', [('control', False), ('hop', True), ('execution', True)])
    def test_peers_from_control_nodes_allowed(self, node_type, allowed, post, admin_user):
        '''
        only hop and execution nodes can have peers_from_control_nodes set to True
        '''
        post(
            url=reverse('api:instance_list'),
            data={"hostname": "abc", "peers_from_control_nodes": True, "node_type": node_type, "listener_port": 6789},
            user=admin_user,
            expect=201 if allowed else 400,
        )

    def test_listener_port_is_required(self, admin_user, post):
        '''
        if adding instance to peers list, that instance must have listener_port set
        '''
        Instance.objects.create(hostname='abc', node_type="hop", listener_port=None)
        post(
            url=reverse('api:instance_list'),
            data={"hostname": "ex", "peers_from_control_nodes": False, "node_type": "execution", "listener_port": None, "peers": ["abc"]},
            user=admin_user,
            expect=400,
        )

    def test_peers_from_control_nodes_listener_port_enabled(self, admin_user, post):
        '''
        if peers_from_control_nodes is True, listener_port must an integer
        Assert that all other combinations are allowed
        '''
        Instance.objects.create(hostname='abc', node_type="control")
        i = 0
        for node_type in ['hop', 'execution']:
            for peers_from in [True, False]:
                for listener_port in [None, 6789]:
                    # only disallowed case is when peers_from is True and listener port is None
                    disallowed = peers_from and not listener_port
                    post(
                        url=reverse('api:instance_list'),
                        data={"hostname": f"abc{i}", "peers_from_control_nodes": peers_from, "node_type": node_type, "listener_port": listener_port},
                        user=admin_user,
                        expect=400 if disallowed else 201,
                    )
                    i += 1

    def test_disallow_modify_peers_control_nodes(self, admin_user, patch):
        '''
        for control nodes, peers field should not be
        modified directly via patch.
        '''
        control = Instance.objects.create(hostname='abc', node_type='control')
        hop1 = Instance.objects.create(hostname='hop1', node_type='hop', peers_from_control_nodes=True, listener_port=6789)
        hop2 = Instance.objects.create(hostname='hop2', node_type='hop', peers_from_control_nodes=False, listener_port=6789)
        assert [hop1] == list(control.peers.all())  # only hop1 should be peered
        patch(
            url=reverse('api:instance_detail', kwargs={'pk': control.pk}),
            data={"peers": ["hop2"]},
            user=admin_user,
            expect=400,  # cannot add peers directly
        )
        patch(
            url=reverse('api:instance_detail', kwargs={'pk': control.pk}),
            data={"peers": ["hop1"]},
            user=admin_user,
            expect=200,  # patching with current peers list should be okay
        )
        patch(
            url=reverse('api:instance_detail', kwargs={'pk': control.pk}),
            data={"peers": []},
            user=admin_user,
            expect=400,  # cannot remove peers directly
        )
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
            expect=200,  # patching without data should be fine too
        )
        control.refresh_from_db()
        assert {hop1, hop2} == set(control.peers.all())  # hop1 and hop2 should now be peered from control node

    def test_disallow_changing_hostname(self, admin_user, patch):
        '''
        cannot change hostname
        '''
        hop = Instance.objects.create(hostname='hop', node_type='hop')
        patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"hostname": "hop2"},
            user=admin_user,
            expect=400,
        )

    def test_disallow_changing_node_state(self, admin_user, patch):
        '''
        only allow setting to deprovisioning
        '''
        hop = Instance.objects.create(hostname='hop', node_type='hop', node_state='installed')
        patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"node_state": "deprovisioning"},
            user=admin_user,
            expect=200,
        )
        patch(
            url=reverse('api:instance_detail', kwargs={'pk': hop.pk}),
            data={"node_state": "ready"},
            user=admin_user,
            expect=400,
        )

    def test_control_node_automatically_peers(self):
        '''
        a new control node should automatically
        peer to hop

        peer to hop should be removed if hop is deleted
        '''

        hop = Instance.objects.create(hostname='hop', node_type='hop', peers_from_control_nodes=True, listener_port=6789)
        control = Instance.objects.create(hostname='abc', node_type='control')
        assert hop in control.peers.all()
        hop.delete()
        assert not control.peers.exists()

    def test_group_vars(self, get, admin_user):
        '''
        control > hop1 > hop2 < execution
        '''
        control = Instance.objects.create(hostname='control', node_type='control', listener_port=None)
        hop1 = Instance.objects.create(hostname='hop1', node_type='hop', listener_port=6789, peers_from_control_nodes=True)
        hop2 = Instance.objects.create(hostname='hop2', node_type='hop', listener_port=6789, peers_from_control_nodes=False)
        execution = Instance.objects.create(hostname='execution', node_type='execution', listener_port=6789)

        execution.peers.add(hop2)
        hop1.peers.add(hop2)

        control_vars = yaml.safe_load(generate_group_vars_all_yml(control))
        hop1_vars = yaml.safe_load(generate_group_vars_all_yml(hop1))
        hop2_vars = yaml.safe_load(generate_group_vars_all_yml(hop2))
        execution_vars = yaml.safe_load(generate_group_vars_all_yml(execution))

        def has_peer(group_vars, peer):
            peers = group_vars.get('receptor_peers', [])
            for p in peers:
                if f"{p['host']}:{p['port']}" == peer:
                    return True
            return False

        # control group vars assertions
        assert control_vars.get('receptor_host_identifier', '') == 'control'
        assert has_peer(control_vars, 'hop1:6789')
        assert not has_peer(control_vars, 'hop2:6789')
        assert not has_peer(control_vars, 'execution:6789')
        assert not control_vars.get('receptor_listener', False)

        # hop1 group vars assertions
        assert hop1_vars.get('receptor_host_identifier', '') == 'hop1'
        assert has_peer(hop1_vars, 'hop2:6789')
        assert not has_peer(hop1_vars, 'execution:6789')
        assert hop1_vars.get('receptor_listener', False)

        # hop2 group vars assertions
        assert hop2_vars.get('receptor_host_identifier', '') == 'hop2'
        assert not has_peer(hop2_vars, 'hop1:6789')
        assert not has_peer(hop2_vars, 'execution:6789')
        assert hop2_vars.get('receptor_listener', False)
        assert hop2_vars.get('receptor_peers', []) == []

        # execution group vars assertions
        assert execution_vars.get('receptor_host_identifier', '') == 'execution'
        assert has_peer(execution_vars, 'hop2:6789')
        assert not has_peer(execution_vars, 'hop1:6789')
        assert execution_vars.get('receptor_listener', False)

    def test_write_receptor_config_called(self):
        '''
        Assert that write_receptor_config is called
        when certain instances are created, or if
        peers_from_control_nodes changes.
        In general, write_receptor_config should only
        be called when necessary, as it will reload
        receptor backend connections which is not trivial.
        '''
        with mock.patch('awx.main.models.ha.schedule_write_receptor_config') as write_method:
            # new control instance but nothing to peer to (no)
            control = Instance.objects.create(hostname='control1', node_type='control')
            write_method.assert_not_called()

            # new hop node with peers_from_control_nodes False (no)
            hop1 = Instance.objects.create(hostname='hop1', node_type='hop', listener_port=6789, peers_from_control_nodes=False)
            hop1.delete()
            write_method.assert_not_called()

            # new hop node with peers_from_control_nodes True (yes)
            hop1 = Instance.objects.create(hostname='hop1', node_type='hop', listener_port=6789, peers_from_control_nodes=True)
            write_method.assert_called()
            write_method.reset_mock()

            # new control instance but with something to peer to (yes)
            Instance.objects.create(hostname='control2', node_type='control')
            write_method.assert_called()
            write_method.reset_mock()

            # new hop node with peers_from_control_nodes False and peered to another hop node (no)
            hop2 = Instance.objects.create(hostname='hop2', node_type='hop', listener_port=6789, peers_from_control_nodes=False)
            hop2.peers.add(hop1)
            hop2.delete()
            write_method.assert_not_called()

            # changing peers_from_control_nodes to False (yes)
            hop1.peers_from_control_nodes = False
            hop1.save()
            write_method.assert_called()
            write_method.reset_mock()

            # deleting hop node that has peers_from_control_nodes to False (no)
            hop1.delete()
            write_method.assert_not_called()

            # deleting control nodes (no)
            control.delete()
            write_method.assert_not_called()

    def test_write_receptor_config_data(self):
        '''
        Assert the correct peers are included in data that will
        be written to receptor.conf
        '''
        from awx.main.tasks.receptor import RECEPTOR_CONFIG_STARTER

        with mock.patch('awx.main.tasks.receptor.read_receptor_config', return_value=list(RECEPTOR_CONFIG_STARTER)):
            from awx.main.tasks.receptor import generate_config_data

            _, should_update = generate_config_data()
            assert not should_update

            # not peered, so config file should not be updated
            for i in range(3):
                Instance.objects.create(hostname=f"exNo-{i}", node_type='execution', listener_port=6789, peers_from_control_nodes=False)

            _, should_update = generate_config_data()
            assert not should_update

            # peered, so config file should be updated
            expected_peers = []
            for i in range(3):
                expected_peers.append(f"hop-{i}:6789")
                Instance.objects.create(hostname=f"hop-{i}", node_type='hop', listener_port=6789, peers_from_control_nodes=True)

            for i in range(3):
                expected_peers.append(f"exYes-{i}:6789")
                Instance.objects.create(hostname=f"exYes-{i}", node_type='execution', listener_port=6789, peers_from_control_nodes=True)

            new_config, should_update = generate_config_data()
            assert should_update

            peers = []
            for entry in new_config:
                for key, value in entry.items():
                    if key == "tcp-peer":
                        peers.append(value['address'])

            assert set(expected_peers) == set(peers)
