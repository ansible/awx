from unittest import mock

from awx.main.management.commands.cleanup_jobs import _pre_delete_job_host_summaries, JHS_CHUNK_SIZE


class TestPreDeleteJobHostSummaries:
    def test_empty_list_is_noop(self):
        with mock.patch('awx.main.management.commands.cleanup_jobs.connection') as mock_conn:
            _pre_delete_job_host_summaries([])
            mock_conn.cursor.assert_not_called()

    def test_single_chunk(self):
        job_pks = [1, 2, 3]
        with mock.patch('awx.main.management.commands.cleanup_jobs.connection') as mock_conn:
            mock_cursor = mock.MagicMock()
            mock_conn.cursor.return_value.__enter__ = mock.Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

            _pre_delete_job_host_summaries(job_pks)

            assert mock_cursor.execute.call_count == 2
            update_call = mock_cursor.execute.call_args_list[0]
            assert 'UPDATE main_host SET last_job_host_summary_id = NULL' in update_call[0][0]
            assert 'ANY(%s)' in update_call[0][0]
            assert update_call[0][1] == [[1, 2, 3]]

            delete_call = mock_cursor.execute.call_args_list[1]
            assert 'DELETE FROM main_jobhostsummary' in delete_call[0][0]
            assert 'ANY(%s)' in delete_call[0][0]
            assert delete_call[0][1] == [[1, 2, 3]]

    def test_multiple_chunks(self):
        job_pks = list(range(1, JHS_CHUNK_SIZE + 500))
        with mock.patch('awx.main.management.commands.cleanup_jobs.connection') as mock_conn:
            mock_cursor = mock.MagicMock()
            mock_conn.cursor.return_value.__enter__ = mock.Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

            _pre_delete_job_host_summaries(job_pks)

            # 2 chunks x 2 SQL statements each = 4 execute calls
            assert mock_cursor.execute.call_count == 4

            # First chunk should have JHS_CHUNK_SIZE items
            first_update = mock_cursor.execute.call_args_list[0]
            assert len(first_update[0][1][0]) == JHS_CHUNK_SIZE

            # Second chunk should have the remainder
            second_update = mock_cursor.execute.call_args_list[2]
            assert len(second_update[0][1][0]) == 499

    def test_sql_is_fully_static(self):
        """SQL strings contain no interpolated values — only ANY(%s) placeholders."""
        job_pks = [100, 200]
        with mock.patch('awx.main.management.commands.cleanup_jobs.connection') as mock_conn:
            mock_cursor = mock.MagicMock()
            mock_conn.cursor.return_value.__enter__ = mock.Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

            _pre_delete_job_host_summaries(job_pks)

            for call in mock_cursor.execute.call_args_list:
                sql = call[0][0]
                assert 'ANY(%s)' in sql
                assert '100' not in sql
                assert '200' not in sql

    def test_logger_called_per_chunk(self):
        job_pks = [1, 2, 3]
        logger = mock.MagicMock()
        with mock.patch('awx.main.management.commands.cleanup_jobs.connection') as mock_conn:
            mock_cursor = mock.MagicMock()
            mock_conn.cursor.return_value.__enter__ = mock.Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

            _pre_delete_job_host_summaries(job_pks, logger=logger)

            logger.debug.assert_called_once()

    def test_update_runs_before_delete(self):
        """Host FK must be NULLed before JHS rows are deleted."""
        job_pks = [1]
        with mock.patch('awx.main.management.commands.cleanup_jobs.connection') as mock_conn:
            mock_cursor = mock.MagicMock()
            mock_conn.cursor.return_value.__enter__ = mock.Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

            _pre_delete_job_host_summaries(job_pks)

            first_sql = mock_cursor.execute.call_args_list[0][0][0]
            second_sql = mock_cursor.execute.call_args_list[1][0][0]
            assert 'UPDATE' in first_sql
            assert 'DELETE' in second_sql


class TestDeleteMetaPreDelete:
    """Verify DeleteMeta.delete_jobs() calls _pre_delete_job_host_summaries correctly."""

    @mock.patch('awx.main.management.commands.cleanup_jobs._pre_delete_job_host_summaries')
    def test_called_for_job_class(self, mock_pre_delete):
        from awx.main.management.commands.cleanup_jobs import DeleteMeta
        from awx.main.models import Job

        dm = DeleteMeta(logger=mock.MagicMock(), job_class=Job, cutoff=mock.MagicMock(), dry_run=False)
        dm.jobs_pk_list = [10, 20, 30]

        with mock.patch.object(Job.objects, 'filter') as mock_filter:
            mock_filter.return_value.delete.return_value = (3, {})
            dm.delete_jobs()

        mock_pre_delete.assert_called_once_with([10, 20, 30], dm.logger)

    @mock.patch('awx.main.management.commands.cleanup_jobs._pre_delete_job_host_summaries')
    def test_skipped_for_non_job_class(self, mock_pre_delete):
        from awx.main.management.commands.cleanup_jobs import DeleteMeta
        from awx.main.models import ProjectUpdate

        dm = DeleteMeta(logger=mock.MagicMock(), job_class=ProjectUpdate, cutoff=mock.MagicMock(), dry_run=False)
        dm.jobs_pk_list = [10, 20]

        with mock.patch.object(ProjectUpdate.objects, 'filter') as mock_filter:
            mock_filter.return_value.delete.return_value = (2, {})
            dm.delete_jobs()

        mock_pre_delete.assert_not_called()

    @mock.patch('awx.main.management.commands.cleanup_jobs._pre_delete_job_host_summaries')
    def test_skipped_for_dry_run(self, mock_pre_delete):
        from awx.main.management.commands.cleanup_jobs import DeleteMeta
        from awx.main.models import Job

        dm = DeleteMeta(logger=mock.MagicMock(), job_class=Job, cutoff=mock.MagicMock(), dry_run=True)
        dm.jobs_pk_list = [10, 20]

        dm.delete_jobs()

        mock_pre_delete.assert_not_called()
