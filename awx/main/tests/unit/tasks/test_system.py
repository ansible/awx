import pytest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch
from awx.main.tasks.system import (
    _heartbeat_instance_management,
    update_inventory_computed_fields,
    inspect_execution_and_hop_nodes,
    _mesh_all_ready_nodes_visible,
    _heartbeat_handle_lost_instances,
    _reap_and_mark_lost_instance,
)
from awx.main.dispatch.reaper import startup_reaping, reap
from awx.main.models import Instance, Inventory
from django.conf import settings
from django.db import DatabaseError
from django.utils.timezone import now, timedelta


# ── Helpers ───────────────────────────────────────────────────────────────────


def _instance(hostname, node_type='execution', node_state='ready', last_seen_secs_ago=0):
    """Build a mock instance. last_seen_secs_ago: how old the last_seen timestamp is."""
    inst = MagicMock()
    inst.hostname = hostname
    inst.node_type = node_type
    inst.node_state = node_state
    inst.last_seen = now() - timedelta(seconds=last_seen_secs_ago)
    return inst


_UNSET = object()  # sentinel so callers can explicitly pass None (JSON null from receptor)


def _mesh_status(known_costs=_UNSET, advertisements=_UNSET):
    return {
        'KnownConnectionCosts': {} if known_costs is _UNSET else known_costs,
        'Advertisements': [] if advertisements is _UNSET else [{'NodeID': n} for n in (advertisements or [])],
    }


def _mock_ctl(status):
    ctl = MagicMock()
    ctl.simple_command.return_value = status
    return ctl


# ── Tests: _mesh_all_ready_nodes_visible ──────────────────────────────────────


class TestMeshAllReadyNodesVisible:
    def test_passes_when_all_nodes_visible(self):
        """Gate passes when all READY EE/hop nodes appear in both tables."""
        nodes = [
            _instance('ee-0', 'execution', 'ready'),
            _instance('ee-1', 'execution', 'ready'),
            _instance('hop-0', 'hop', 'ready'),
            _instance('ctrl-0', 'control', 'ready'),  # controls never checked
        ]
        status = _mesh_status(
            known_costs={'ee-0': {}, 'ee-1': {}, 'hop-0': {}},
            advertisements=['ee-0', 'ee-1', 'hop-0'],
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_blocks_window_a_ee_absent_from_routing(self):
        """Gate blocks (Window A) when EEs absent from KnownConnectionCosts.

        Scenario: fresh receptor after controller restart — routing table not yet propagated.
        """
        nodes = [_instance('ee-0'), _instance('ee-1')]
        status = _mesh_status(
            known_costs={'ctrl-0': {}},  # EEs not in routing table yet
            advertisements=['ee-0', 'ee-1'],
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            assert _mesh_all_ready_nodes_visible(nodes) is False

    def test_blocks_window_b_ee_absent_from_advertisements(self):
        """Gate blocks (Window B) when EEs are routable but not yet advertising.

        Scenario: t=3-60s after restart — routing propagated but EEs haven't
        re-advertised yet (advertisement period = 60s, fresh receptor has no cache).
        """
        nodes = [_instance('ee-0'), _instance('ee-1')]
        status = _mesh_status(
            known_costs={'ee-0': {}, 'ee-1': {}},  # routing restored
            advertisements=['ctrl-0'],  # but no EE advertisements yet
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            assert _mesh_all_ready_nodes_visible(nodes) is False

    def test_fails_open_when_receptor_socket_missing(self):
        """Gate fails open on FileNotFoundError (receptor not yet started)."""
        nodes = [_instance('ee-0')]
        with patch('awx.main.tasks.system.get_receptor_ctl', side_effect=FileNotFoundError):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_fails_open_when_receptor_status_fails(self):
        """Gate fails open when receptorctl status raises ValueError."""
        nodes = [_instance('ee-0')]
        ctl = MagicMock()
        ctl.simple_command.side_effect = ValueError('connection reset')
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=ctl):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_fails_open_on_oserror(self):
        """Gate fails open on OSError (stale socket — exists but daemon not accepting).

        A present-but-unresponsive socket raises OSError/ConnectionRefusedError, not
        FileNotFoundError. This is the exact scenario during a controller restart window.
        """
        nodes = [_instance('ee-0')]
        with patch('awx.main.tasks.system.get_receptor_ctl', side_effect=OSError('Connection refused')):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_fails_open_on_runtime_error(self):
        """Gate fails open on RuntimeError (receptor handshake or protocol error)."""
        nodes = [_instance('ee-0')]
        ctl = MagicMock()
        ctl.simple_command.side_effect = RuntimeError('Failed to connect to Receptor socket')
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=ctl):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_fails_open_when_receptor_returns_null_known_costs(self):
        """Gate fails open when KnownConnectionCosts is JSON null (Go nil map → Python None).

        Receptor is a Go service; a nil map marshals to JSON null, which Python's json
        decoder represents as None. This is most likely during Window A (fresh startup
        with no established connections yet). set(None) would raise TypeError without
        the `or {}` guard.
        """
        nodes = [_instance('ee-0')]
        status = _mesh_status(known_costs=None, advertisements=['ee-0'])
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            # None KnownConnectionCosts → ee-0 absent from routing → gate blocks (Window A)
            assert _mesh_all_ready_nodes_visible(nodes) is False

    def test_fails_open_when_receptor_returns_null_advertisements(self):
        """Gate blocks when Advertisements is JSON null (Go nil slice → Python None).

        This is Window B: routing is established but no service advertisements yet.
        `for ad in None` would raise TypeError without the `or []` guard.
        """
        nodes = [_instance('ee-0')]
        status = _mesh_status(known_costs={'ee-0': {}}, advertisements=None)
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            # None Advertisements → ee-0 absent from ads → gate blocks (Window B)
            assert _mesh_all_ready_nodes_visible(nodes) is False

    def test_passes_trivially_with_no_ee_or_hop_nodes(self):
        """Gate passes immediately when instance_list has only control nodes.

        No receptor call is made — nothing to check.
        """
        nodes = [_instance('ctrl-0', 'control', 'ready')]
        with patch('awx.main.tasks.system.get_receptor_ctl') as mock_ctl:
            assert _mesh_all_ready_nodes_visible(nodes) is True
        mock_ctl.assert_not_called()

    def test_receptor_not_called_when_expected_set_is_empty(self):
        """Gate returns True without calling receptor when no READY EE/hop nodes exist.

        If `expected` is empty (e.g. control-only cluster, or all EEs are UNAVAILABLE),
        the gate short-circuits before making a receptor call. This also validates that
        control nodes are never included in the expected set.
        """
        nodes = [
            _instance('ctrl-0', 'control', 'ready'),
            _instance('ee-down', 'execution', 'unavailable'),
        ]
        with patch('awx.main.tasks.system.get_receptor_ctl') as mock_ctl:
            assert _mesh_all_ready_nodes_visible(nodes) is True
        mock_ctl.assert_not_called()

    def test_ignores_unavailable_ee_nodes(self):
        """Gate only checks READY nodes — already-UNAVAILABLE EEs are excluded.

        An EE that is already UNAVAILABLE should not be in expected; the gate
        should not fail if that EE is missing from the mesh tables.
        """
        nodes = [
            _instance('ee-down', 'execution', 'unavailable'),
            _instance('ee-up', 'execution', 'ready'),
        ]
        status = _mesh_status(
            known_costs={'ee-up': {}},  # only the READY EE present
            advertisements=['ee-up'],
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_excludes_genuinely_dead_node_from_expected(self):
        """Gate does not block indefinitely on a genuinely dead node.

        A dead node stays in READY state until lost-instance handling runs.
        Its last_seen is >= is_lost threshold (2 × HEARTBEAT_PERIOD = 120s), which
        is past the 1.5 × HEARTBEAT_PERIOD recency cutoff (90s). The gate must
        exclude it from expected so its mesh absence does not defer peer judgment
        on every subsequent heartbeat cycle.
        """
        dead_node = _instance('dead-ee', last_seen_secs_ago=settings.CLUSTER_NODE_HEARTBEAT_PERIOD * 3)
        live_node = _instance('live-ee')
        status = _mesh_status(
            known_costs={'live-ee': {}},  # dead-ee absent (genuinely offline)
            advertisements=['live-ee'],
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            assert _mesh_all_ready_nodes_visible([dead_node, live_node]) is True

    def test_instance_list_plus_lost_covers_removed_ees(self):
        """Caller must pass instance_list + lost_instances, not just instance_list.

        The peer-judgment loop removes lost EEs from instance_list before the gate
        runs. If only instance_list is passed, expected is empty and the gate always
        returns True. This test proves the gate correctly catches Window B when given
        the combined list (nodes must have recent last_seen to be included).
        """
        ee0 = _instance('ee-0')
        ee1 = _instance('ee-1')

        # Simulate the state after peer-judgment loop:
        # instance_list had EEs removed; lost_instances holds them.
        instance_list_after_loop = []  # EEs already removed
        lost_instances = [ee0, ee1]  # peer-judgment put them here

        status = _mesh_status(
            known_costs={'ee-0': {}, 'ee-1': {}},
            advertisements=['ctrl-0'],  # no EE ads → Window B
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            # Wrong: passing only instance_list (empty) → gate returns True (bug)
            assert _mesh_all_ready_nodes_visible(instance_list_after_loop) is True

            # Correct: passing combined list → gate catches Window B (returns False)
            assert _mesh_all_ready_nodes_visible(instance_list_after_loop + lost_instances) is False


# ── Tests: _heartbeat_handle_lost_instances (task manager lock) ───────────────


def _make_lock(acquired):
    """Return a context manager factory that always yields the given acquired bool."""

    @contextmanager
    def _lock(name, wait=True, **kwargs):
        yield acquired

    return _lock


def _make_lock_sequence(sequence):
    """Return a context manager factory that yields values from sequence in order."""
    it = iter(sequence)

    @contextmanager
    def _lock(name, wait=True, **kwargs):
        yield next(it)

    return _lock


def _lost_instance(hostname='ctrl-1'):
    inst = MagicMock()
    inst.hostname = hostname
    inst.node_type = 'control'
    inst.node_state = 'ready'
    return inst


class TestHeartbeatHandleLostInstancesLock:
    def _run(self, lost, this_inst=None):
        if this_inst is None:
            this_inst = MagicMock()
        with (
            patch('awx.main.tasks.system.reaper') as mock_reaper,
            patch('awx.main.tasks.system.UnifiedJob') as mock_uj,
            patch('awx.main.tasks.system.settings') as mock_settings,
        ):
            mock_settings.AWX_AUTO_DEPROVISION_INSTANCES = False
            _heartbeat_handle_lost_instances(lost, this_inst)
            return mock_reaper, mock_uj

    def test_processes_instance_when_lock_acquired(self):
        """When the lock is acquired, reap and mark_offline are both called."""
        inst = _lost_instance()
        with patch('awx.main.tasks.system.advisory_lock', _make_lock(True)):
            mock_reaper, _ = self._run([inst])
        mock_reaper.reap.assert_called_once_with(inst, job_explanation='Job reaped due to instance shutdown', undispatched_only=True)
        inst.mark_offline.assert_called_once()

    def test_skips_instance_when_lock_unavailable(self):
        """When the lock is unavailable, reap and mark_offline are not called."""
        inst = _lost_instance()
        with patch('awx.main.tasks.system.advisory_lock', _make_lock(False)):
            mock_reaper, _ = self._run([inst])
        mock_reaper.reap.assert_not_called()
        inst.mark_offline.assert_not_called()

    def test_logs_when_instance_deferred(self):
        """When the lock is unavailable, a log message is emitted with the hostname."""
        inst = _lost_instance('ctrl-1')
        with patch('awx.main.tasks.system.advisory_lock', _make_lock(False)), patch('awx.main.tasks.system.logger') as mock_log:
            self._run([inst])
        assert mock_log.info.called
        logged = mock_log.info.call_args[0][0]
        assert 'ctrl-1' in logged

    def test_per_instance_lock_first_skipped_second_processed(self):
        """Lock alternates False/True: first instance skipped, second processed."""
        inst1 = _lost_instance('ctrl-1')
        inst2 = _lost_instance('ctrl-2')
        with patch('awx.main.tasks.system.advisory_lock', _make_lock_sequence([False, True])):
            mock_reaper, _ = self._run([inst1, inst2])
        mock_reaper.reap.assert_called_once_with(inst2, job_explanation='Job reaped due to instance shutdown', undispatched_only=True)
        inst1.mark_offline.assert_not_called()
        inst2.mark_offline.assert_called_once()

    def test_all_instances_processed_when_lock_always_acquired(self):
        """When lock is always acquired, all instances are fully processed."""
        inst1 = _lost_instance('ctrl-1')
        inst2 = _lost_instance('ctrl-2')
        with patch('awx.main.tasks.system.advisory_lock', _make_lock(True)):
            mock_reaper, _ = self._run([inst1, inst2])
        assert mock_reaper.reap.call_count == 2
        inst1.mark_offline.assert_called_once()
        inst2.mark_offline.assert_called_once()


# ── Tests: _reap_and_mark_lost_instance (exception / branch coverage) ────────


class TestReapAndMarkLostInstance:
    def _run(self, inst, auto_deprovision=False, reap_side_effect=None, mark_offline_side_effect=None):
        with (
            patch('awx.main.tasks.system.reaper') as mock_reaper,
            patch('awx.main.tasks.system.UnifiedJob'),
            patch('awx.main.tasks.system.settings') as mock_s,
        ):
            mock_s.AWX_AUTO_DEPROVISION_INSTANCES = auto_deprovision
            if reap_side_effect is not None:
                mock_reaper.reap.side_effect = reap_side_effect
            if mark_offline_side_effect is not None:
                inst.mark_offline.side_effect = mark_offline_side_effect
            _reap_and_mark_lost_instance(inst)
        return mock_reaper

    def test_reap_exception_does_not_prevent_mark_offline(self):
        """Exception during reap is logged but mark_offline still runs.

        The first try block isolates reap/update failures from the mark-offline logic.
        """
        inst = _lost_instance()
        self._run(inst, reap_side_effect=Exception('receptor timeout'))
        inst.mark_offline.assert_called_once()

    def test_auto_deprovision_deletes_control_node(self):
        """AWX_AUTO_DEPROVISION_INSTANCES=True: control node is deleted, not marked offline."""
        inst = _lost_instance()
        inst.node_type = 'control'
        self._run(inst, auto_deprovision=True)
        inst.delete.assert_called_once()
        inst.mark_offline.assert_not_called()

    def test_skips_mark_offline_when_node_already_unavailable(self):
        """Node in a non-READY state is not marked offline again (it's already handled)."""
        inst = _lost_instance()
        inst.node_state = 'unavailable'
        self._run(inst)
        inst.mark_offline.assert_not_called()

    def test_database_error_without_sqlstate_logs_exception(self):
        """DatabaseError with no __cause__ sqlstate logs the generic error message."""
        inst = _lost_instance()
        err = DatabaseError('constraint violation')
        err.__cause__ = None
        with patch('awx.main.tasks.system.logger') as mock_log:
            self._run(inst, mark_offline_side_effect=err)
        assert mock_log.exception.called
        assert 'No SQL state' in mock_log.exception.call_args[0][0]

    def test_database_error_with_sqlstate_logs_details(self):
        """DatabaseError with a cause.sqlstate invokes psycopg.errors.lookup for the state string."""
        inst = _lost_instance()
        err = DatabaseError('unique violation')

        class _FakePsycopgError(Exception):
            sqlstate = 'some_state'

        err.__cause__ = _FakePsycopgError('underlying pg error')
        with (
            patch('awx.main.tasks.system.logger') as mock_log,
            patch('awx.main.tasks.system.psycopg') as mock_psycopg,
        ):
            mock_psycopg.errors.lookup.return_value = 'SomeError'
            mock_psycopg.errors.NoData = 'other_state'  # ensure non-NoData branch
            self._run(inst, mark_offline_side_effect=err)
        mock_psycopg.errors.lookup.assert_called_once_with('some_state')
        assert mock_log.exception.called

    def test_database_error_with_nodata_sqlstate_logs_debug(self):
        """NoData sqlstate means another controller already marked the instance lost — log at debug."""
        inst = _lost_instance()
        err = DatabaseError('nodata')

        class _FakePsycopgError(Exception):
            sqlstate = 'nodata_state'

        err.__cause__ = _FakePsycopgError('nodata cause')
        with (
            patch('awx.main.tasks.system.logger') as mock_log,
            patch('awx.main.tasks.system.psycopg') as mock_psycopg,
        ):
            mock_psycopg.errors.lookup.return_value = 'NoData'
            mock_psycopg.errors.NoData = 'nodata_state'  # match the sqlstate
            self._run(inst, mark_offline_side_effect=err)
        mock_log.exception.assert_not_called()
        debug_messages = [str(call) for call in mock_log.debug.call_args_list]
        assert any('marked' in m for m in debug_messages)


# ── Tests: work_unit_id filter (AAP-89598) ───────────────────────────────────


class TestWorkUnitIdFilter:
    def test_startup_reaping_excludes_dispatched_jobs(self):
        """startup_reaping filters on work_unit_id='' so dispatched EE jobs are never reaped on restart."""
        with (
            patch('awx.main.dispatch.reaper.UnifiedJob.objects.filter') as mock_filter,
            patch('awx.main.dispatch.reaper.Instance.objects.my_hostname', return_value='ctrl-1'),
        ):
            mock_filter.return_value = []
            startup_reaping()
        mock_filter.assert_called_once_with(status='running', controller_node='ctrl-1', work_unit_id='')

    def test_reap_undispatched_only_excludes_dispatched_jobs(self):
        """reap(undispatched_only=True) adds work_unit_id='' to the queryset filter."""
        with (
            patch('awx.main.dispatch.reaper.UnifiedJob.objects.filter') as mock_filter,
            patch('awx.main.dispatch.reaper.Instance.objects.my_hostname', return_value='ctrl-1'),
            patch('awx.main.dispatch.reaper.ContentType.objects.get_for_model') as mock_ct,
        ):
            mock_ct.return_value.id = 99
            mock_filter.return_value = []
            reap(undispatched_only=True)
        q_obj = mock_filter.call_args[0][0]
        # The Q tree must contain the work_unit_id='' leaf
        assert _q_contains(q_obj, 'work_unit_id', '')

    def test_reap_default_includes_dispatched_jobs(self):
        """reap() without undispatched_only does not add work_unit_id filter (existing behaviour)."""
        with (
            patch('awx.main.dispatch.reaper.UnifiedJob.objects.filter') as mock_filter,
            patch('awx.main.dispatch.reaper.Instance.objects.my_hostname', return_value='ctrl-1'),
            patch('awx.main.dispatch.reaper.ContentType.objects.get_for_model') as mock_ct,
        ):
            mock_ct.return_value.id = 99
            mock_filter.return_value = []
            reap()
        q_obj = mock_filter.call_args[0][0]
        assert not _q_contains(q_obj, 'work_unit_id', '')

    def test_peer_reaper_passes_undispatched_only(self):
        """_reap_and_mark_lost_instance calls reaper.reap with undispatched_only=True.

        Dispatched jobs on a dead peer are left untouched so AAP-89602 adoption can pick them up.
        """
        inst = _lost_instance('ctrl-1')
        with (
            patch('awx.main.tasks.system.advisory_lock', _make_lock(True)),
            patch('awx.main.tasks.system.reaper') as mock_reaper,
            patch('awx.main.tasks.system.UnifiedJob'),
            patch('awx.main.tasks.system.settings') as mock_settings,
        ):
            mock_settings.AWX_AUTO_DEPROVISION_INSTANCES = False
            _heartbeat_handle_lost_instances([inst], MagicMock())
        mock_reaper.reap.assert_called_once_with(inst, job_explanation='Job reaped due to instance shutdown', undispatched_only=True)


def _q_contains(q, key, value):
    """Recursively check whether a Q object tree contains a (key, value) leaf."""
    for child in q.children:
        if isinstance(child, tuple) and child == (key, value):
            return True
        if hasattr(child, 'children') and _q_contains(child, key, value):
            return True
    return False


@pytest.fixture
def mock_logger():
    with patch("awx.main.tasks.system.logger") as logger:
        yield logger


@pytest.fixture
def mock_inventory():
    return MagicMock(spec=Inventory)


def test_update_inventory_computed_fields_existing_inventory(mock_logger, mock_inventory):
    # Mocking the Inventory.objects.filter method to return a non-empty queryset
    with patch("awx.main.tasks.system.Inventory.objects.filter") as mock_filter:
        mock_filter.return_value.exists.return_value = True
        mock_filter.return_value.__getitem__.return_value = mock_inventory

        # Mocking the update_computed_fields method
        with patch.object(mock_inventory, "update_computed_fields") as mock_update_computed_fields:
            update_inventory_computed_fields(1)

            # Assertions
            mock_filter.assert_called_once_with(id=1)
            mock_update_computed_fields.assert_called_once()

            # You can add more assertions based on your specific requirements


def test_update_inventory_computed_fields_missing_inventory(mock_logger):
    # Mocking the Inventory.objects.filter method to return an empty queryset
    with patch("awx.main.tasks.system.Inventory.objects.filter") as mock_filter:
        mock_filter.return_value.exists.return_value = False

        update_inventory_computed_fields(1)

        # Assertions
        mock_filter.assert_called_once_with(id=1)
        mock_logger.error.assert_called_once_with("Update Inventory Computed Fields failed due to missing inventory: 1")


def test_update_inventory_computed_fields_database_error_nosqlstate(mock_logger, mock_inventory):
    # Mocking the Inventory.objects.filter method to return a non-empty queryset
    with patch("awx.main.tasks.system.Inventory.objects.filter") as mock_filter:
        mock_filter.return_value.exists.return_value = True
        mock_filter.return_value.__getitem__.return_value = mock_inventory

        # Mocking the update_computed_fields method
        with patch.object(mock_inventory, "update_computed_fields") as mock_update_computed_fields:
            # Simulating the update_computed_fields method to explicitly raise a DatabaseError
            mock_update_computed_fields.side_effect = DatabaseError("Some error")

            update_inventory_computed_fields(1)

            # Assertions
            mock_filter.assert_called_once_with(id=1)
            mock_update_computed_fields.assert_called_once()
            mock_inventory.update_computed_fields.assert_called_once()


@patch('awx.main.tasks.system.inspect_execution_and_hop_nodes')
@patch('awx.main.tasks.system._mesh_all_ready_nodes_visible', return_value=False)
@patch('awx.main.tasks.system.get_receptor_ctl')
@patch('awx.main.tasks.system.Instance.objects.filter')
def test_heartbeat_defers_lost_instances_when_mesh_gate_blocks(mock_filter, mock_get_ctl, mock_gate, mock_inspect):
    """When the mesh gate returns False, lost_instances is returned empty (peer judgment deferred)."""
    this_inst = MagicMock(spec=Instance)
    this_inst.hostname = 'ctrl-0'
    this_inst.is_lost.return_value = False
    this_inst.last_seen = now() - timedelta(seconds=30)

    lost_peer = MagicMock(spec=Instance)
    lost_peer.hostname = 'ctrl-1'
    lost_peer.is_lost.return_value = True

    mock_filter.return_value = [this_inst, lost_peer]

    with patch('awx.main.tasks.system.settings') as mock_settings:
        mock_settings.CLUSTER_HOST_ID = 'ctrl-0'
        mock_settings.CLUSTER_NODE_HEARTBEAT_PERIOD = 60
        _, _, lost_result = _heartbeat_instance_management()

    assert lost_result == []
    mock_gate.assert_called_once()


@patch('awx.main.tasks.system.get_receptor_ctl', side_effect=FileNotFoundError)
@patch('awx.main.tasks.system.Instance.objects.filter')
def test_heartbeat_marks_offline_when_receptor_unavailable(mock_filter, mock_get_ctl):
    this_inst = MagicMock(spec=Instance)
    this_inst.hostname = 'test-host'
    mock_filter.return_value = [this_inst]

    with patch('awx.main.tasks.system.settings') as mock_settings:
        mock_settings.CLUSTER_HOST_ID = 'test-host'
        result = _heartbeat_instance_management()

    assert result == (None, None, None)
    this_inst.local_health_check.assert_called_once()
    this_inst.mark_offline.assert_called_once_with(errors='Receptor not available')


class TestInspectExecutionAndHopNodes:
    """Tests for the advisory_lock guard in inspect_execution_and_hop_nodes."""

    @patch('awx.main.tasks.system.inspect_established_receptor_connections')
    @patch('awx.main.tasks.system.advisory_lock')
    def test_skips_when_lock_not_acquired(self, mock_lock, mock_inspect_conns):
        mock_lock.return_value.__enter__ = MagicMock(return_value=False)
        mock_lock.return_value.__exit__ = MagicMock(return_value=False)
        receptor_ctl = MagicMock()

        inspect_execution_and_hop_nodes([], receptor_ctl)

        receptor_ctl.simple_command.assert_not_called()
        mock_inspect_conns.assert_not_called()

    @patch('awx.main.tasks.system.inspect_established_receptor_connections')
    @patch('awx.main.tasks.system.advisory_lock')
    def test_runs_when_lock_acquired(self, mock_lock, mock_inspect_conns):
        mock_lock.return_value.__enter__ = MagicMock(return_value=True)
        mock_lock.return_value.__exit__ = MagicMock(return_value=False)
        receptor_ctl = MagicMock()
        receptor_ctl.simple_command.return_value = {'Advertisements': [], 'KnownConnectionCosts': {}}

        inspect_execution_and_hop_nodes([], receptor_ctl)

        receptor_ctl.simple_command.assert_called_once_with('status')
        mock_inspect_conns.assert_called_once()

    @patch('awx.main.tasks.system.inspect_established_receptor_connections')
    @patch('awx.main.tasks.system.advisory_lock')
    def test_updates_last_seen_for_execution_nodes(self, mock_lock, mock_inspect_conns):
        mock_lock.return_value.__enter__ = MagicMock(return_value=True)
        mock_lock.return_value.__exit__ = MagicMock(return_value=False)

        exec_node = MagicMock(spec=Instance)
        exec_node.hostname = 'exec-1'
        exec_node.node_type = 'execution'
        exec_node.node_state = 'ready'
        exec_node.last_seen = None
        exec_node.capacity = 100
        exec_node.enabled = True
        exec_node.cpu = 4
        exec_node.memory = 8000000000

        control_node = MagicMock(spec=Instance)
        control_node.hostname = 'control-1'
        control_node.node_type = 'control'

        receptor_ctl = MagicMock()
        receptor_ctl.simple_command.return_value = {
            'Advertisements': [
                {'NodeID': 'exec-1', 'Time': '2026-01-01T00:00:00+00:00'},
                {'NodeID': 'control-1', 'Time': '2026-01-01T00:00:00+00:00'},
            ],
            'KnownConnectionCosts': {},
        }

        inspect_execution_and_hop_nodes([exec_node, control_node], receptor_ctl)

        exec_node.save.assert_called_once_with(update_fields=['last_seen'])
        control_node.save.assert_not_called()
