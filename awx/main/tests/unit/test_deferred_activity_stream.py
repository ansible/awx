"""Unit tests for deferred_activity_stream context manager and deferral logic in activity_stream_delete."""

from unittest.mock import patch, MagicMock

import pytest

from awx.main.signals import (
    activity_stream_delete,
    deferred_activity_stream,
    _deferred_awx_activity_stream,
)


class _FakeInstance:
    """Minimal stand-in that passes activity_stream_delete guard clauses.

    Not a subclass of Inventory, Host, or Group (isinstance checks fall through).
    Class-level _deferred is False so the getattr guard passes.
    """

    _deferred = False

    class _meta:
        model_name = 'organization'


@pytest.fixture(autouse=True)
def _reset_deferred_state():
    """Guarantee clean deferred state around every test."""
    _deferred_awx_activity_stream.active = False
    _deferred_awx_activity_stream.pending = []
    yield
    _deferred_awx_activity_stream.active = False
    _deferred_awx_activity_stream.pending = []


@pytest.fixture
def delete_deps():
    """Patch model-layer dependencies so activity_stream_delete reaches deferral logic.

    Yields a dict with get_as_class, as_model, and connection mocks.
    """
    with patch('awx.main.signals.activity_stream_enabled', True), patch('awx.main.signals.model_serializer_mapping', return_value={}), patch(
        'awx.main.signals.model_to_dict', return_value={}
    ), patch('awx.main.signals.get_current_user_or_none', return_value=None), patch(
        'awx.main.signals.camelcase_to_underscore', return_value='organization'
    ), patch(
        'awx.main.signals.get_activity_stream_class'
    ) as mock_get_as, patch(
        'awx.main.signals.ActivityStream'
    ) as mock_as_model, patch(
        'awx.main.signals.connection'
    ) as mock_conn:
        yield {
            'get_as_class': mock_get_as,
            'as_model': mock_as_model,
            'connection': mock_conn,
        }


class TestDeferredActivityStream:
    """Tests for the deferred_activity_stream context manager and its
    interaction with activity_stream_delete."""

    def test_deferred_activity_stream_bulk_creates(self, delete_deps):
        """Entries accumulate during deferral -- save() is never called
        individually and bulk_create fires once on context exit."""
        mock_entry_1 = MagicMock(name='entry_1')
        mock_entry_2 = MagicMock(name='entry_2')
        delete_deps['get_as_class'].return_value = MagicMock(
            side_effect=[mock_entry_1, mock_entry_2],
        )

        with deferred_activity_stream():
            instance = _FakeInstance()
            activity_stream_delete(type(instance), instance=instance)
            activity_stream_delete(type(instance), instance=instance)

            mock_entry_1.save.assert_not_called()
            mock_entry_2.save.assert_not_called()

        delete_deps['as_model'].objects.bulk_create.assert_called_once_with(
            [mock_entry_1, mock_entry_2],
        )

    def test_deferred_activity_stream_reentrant(self):
        """Inner context is a no-op; only the outermost caller flushes."""
        mock_entry_1 = MagicMock(name='entry_1')
        mock_entry_2 = MagicMock(name='entry_2')

        with patch('awx.main.signals.ActivityStream') as mock_as_model, patch('awx.main.signals.connection'):
            with deferred_activity_stream():
                _deferred_awx_activity_stream.pending.append(
                    (mock_entry_1, MagicMock()),
                )

                with deferred_activity_stream():
                    assert _deferred_awx_activity_stream.active is True
                    _deferred_awx_activity_stream.pending.append(
                        (mock_entry_2, MagicMock()),
                    )

                # Inner exit must not flush
                assert len(_deferred_awx_activity_stream.pending) == 2
                mock_as_model.objects.bulk_create.assert_not_called()

            # Outer exit flushes all accumulated entries
            mock_as_model.objects.bulk_create.assert_called_once()
            bulk_created = mock_as_model.objects.bulk_create.call_args[0][0]
            assert bulk_created == [mock_entry_1, mock_entry_2]

    @patch('awx.main.signals.connection')
    @patch('awx.main.signals.ActivityStream')
    def test_deferred_activity_stream_discards_on_exception(self, mock_as_model, _mock_conn):
        """Accumulated entries are discarded (not saved) when the body raises."""
        mock_entry = MagicMock(name='entry')

        def _run():
            with deferred_activity_stream():
                _deferred_awx_activity_stream.pending.append(
                    (mock_entry, MagicMock()),
                )
                raise ValueError('boom')

        with pytest.raises(ValueError, match='boom'):
            _run()

        mock_as_model.objects.bulk_create.assert_not_called()
        mock_entry.save.assert_not_called()
        assert _deferred_awx_activity_stream.pending == []

    def test_deferred_activity_stream_on_commit_callbacks(self, delete_deps):
        """Callbacks from accumulated entries are registered via on_commit
        during flush."""
        mock_entry = MagicMock(name='entry')
        delete_deps['get_as_class'].return_value = MagicMock(
            return_value=mock_entry,
        )

        with deferred_activity_stream():
            activity_stream_delete(type(_FakeInstance()), instance=_FakeInstance())

        delete_deps['connection'].on_commit.assert_called_once()
        registered_cb = delete_deps['connection'].on_commit.call_args[0][0]
        assert callable(registered_cb)

    def test_activity_stream_delete_without_deferral(self, delete_deps):
        """Normal (non-deferred) path: entry is saved immediately and
        on_commit is registered directly."""
        mock_entry = MagicMock(name='entry')
        delete_deps['get_as_class'].return_value = MagicMock(
            return_value=mock_entry,
        )

        activity_stream_delete(type(_FakeInstance()), instance=_FakeInstance())

        mock_entry.save.assert_called_once()
        delete_deps['connection'].on_commit.assert_called_once()
        delete_deps['as_model'].objects.bulk_create.assert_not_called()

    @patch('awx.main.signals.connection')
    @patch('awx.main.signals.ActivityStream')
    def test_deferred_flag_state_success(self, _mock_as, _mock_conn):
        """active flag is True inside the context and False after successful exit."""
        assert _deferred_awx_activity_stream.active is False
        with deferred_activity_stream():
            assert _deferred_awx_activity_stream.active is True
        assert _deferred_awx_activity_stream.active is False

    @patch('awx.main.signals.connection')
    @patch('awx.main.signals.ActivityStream')
    def test_deferred_flag_state_exception(self, _mock_as, _mock_conn):
        """active flag is True inside the context and False after exception exit."""
        assert _deferred_awx_activity_stream.active is False

        def _run_and_raise():
            with deferred_activity_stream():
                assert _deferred_awx_activity_stream.active is True
                raise RuntimeError('test error')

        with pytest.raises(RuntimeError, match='test error'):
            _run_and_raise()

        assert _deferred_awx_activity_stream.active is False

    def test_deferred_path_calls_prepare_denormalized_fields(self, delete_deps):
        """Deferred entries have _prepare_denormalized_fields called before
        bulk_create so that deleted_actor and action_node are populated."""
        mock_entry = MagicMock(name='entry')
        delete_deps['get_as_class'].return_value = MagicMock(return_value=mock_entry)

        with deferred_activity_stream():
            activity_stream_delete(type(_FakeInstance()), instance=_FakeInstance())

        mock_entry._prepare_denormalized_fields.assert_called_once()
        delete_deps['as_model'].objects.bulk_create.assert_called_once_with([mock_entry])
