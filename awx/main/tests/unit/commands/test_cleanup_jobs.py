import datetime
from unittest import mock

from django.utils.timezone import now

from awx.main.management.commands.cleanup_jobs import Command, _pre_delete_job_host_summaries, JHS_CHUNK_SIZE


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

            assert mock_cursor.execute.call_count == 1
            delete_call = mock_cursor.execute.call_args_list[0]
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

            # 2 chunks x 1 DELETE each = 2 execute calls
            assert mock_cursor.execute.call_count == 2

            # First chunk should have JHS_CHUNK_SIZE items
            first_delete = mock_cursor.execute.call_args_list[0]
            assert len(first_delete[0][1][0]) == JHS_CHUNK_SIZE

            # Second chunk should have the remainder
            second_delete = mock_cursor.execute.call_args_list[1]
            assert len(second_delete[0][1][0]) == 499

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


class TestCleanupJobsCommand:
    def _make_command(self, batch_size=10, dry_run=False):
        cmd = Command()
        cmd.batch_size = batch_size
        cmd.dry_run = dry_run
        cmd.cutoff = now() - datetime.timedelta(days=1)
        cmd.logger = mock.MagicMock()
        return cmd

    def test_empty_gap_batches_no_keyerror(self):
        """Batch windows over ID gaps return (0, {}) — must not raise KeyError."""
        cmd = self._make_command(batch_size=10)

        mock_batch = mock.MagicMock()
        mock_batch.values_list.return_value = []
        mock_batch.delete.return_value = (0, {})

        mock_qs = mock.MagicMock()
        mock_qs.aggregate.return_value = {'min': 2, 'max': 1000}
        mock_qs.filter.return_value = mock_batch

        mock_filter_qs = mock.MagicMock()
        mock_combined = mock.MagicMock()
        mock_combined.count.return_value = 5
        mock_filter_qs.__or__ = mock.Mock(return_value=mock_combined)

        with mock.patch('awx.main.management.commands.cleanup_jobs.Job') as MockJob, mock.patch(
            'awx.main.management.commands.cleanup_jobs._pre_delete_job_host_summaries'
        ), mock.patch.object(cmd, '_delete_unpartitioned_events'):
            MockJob.objects.filter.return_value = mock_filter_qs
            MockJob.objects.select_related.return_value.filter.return_value.exclude.return_value = mock_qs
            skipped, deleted = cmd.cleanup_jobs()

        assert skipped == 5
        assert deleted == 0

    def test_mixed_batches_sum_correctly(self):
        """Batches returning {} and {'main.Job': N} are summed correctly."""
        cmd = self._make_command(batch_size=10)

        # 3 batches for range(1, 31, 10): first empty, second has 2 jobs, third empty
        mock_batch = mock.MagicMock()
        mock_batch.values_list.return_value = []
        mock_batch.delete.side_effect = [(0, {}), (2, {'main.Job': 2}), (0, {})]

        mock_qs = mock.MagicMock()
        mock_qs.aggregate.return_value = {'min': 1, 'max': 30}
        mock_qs.filter.return_value = mock_batch

        mock_filter_qs = mock.MagicMock()
        mock_combined = mock.MagicMock()
        mock_combined.count.return_value = 0
        mock_filter_qs.__or__ = mock.Mock(return_value=mock_combined)

        with mock.patch('awx.main.management.commands.cleanup_jobs.Job') as MockJob, mock.patch(
            'awx.main.management.commands.cleanup_jobs._pre_delete_job_host_summaries'
        ), mock.patch.object(cmd, '_delete_unpartitioned_events'):
            MockJob.objects.filter.return_value = mock_filter_qs
            MockJob.objects.select_related.return_value.filter.return_value.exclude.return_value = mock_qs
            skipped, deleted = cmd.cleanup_jobs()

        assert deleted == 2

    def test_no_eligible_jobs_skips_loop(self):
        """When aggregate returns min=None the batch loop is skipped entirely."""
        cmd = self._make_command()

        mock_qs = mock.MagicMock()
        mock_qs.aggregate.return_value = {'min': None, 'max': None}

        mock_filter_qs = mock.MagicMock()
        mock_combined = mock.MagicMock()
        mock_combined.count.return_value = 10
        mock_filter_qs.__or__ = mock.Mock(return_value=mock_combined)

        with mock.patch('awx.main.management.commands.cleanup_jobs.Job') as MockJob, mock.patch(
            'awx.main.management.commands.cleanup_jobs._pre_delete_job_host_summaries'
        ) as mock_pre, mock.patch.object(cmd, '_delete_unpartitioned_events'):
            MockJob.objects.filter.return_value = mock_filter_qs
            MockJob.objects.select_related.return_value.filter.return_value.exclude.return_value = mock_qs
            skipped, deleted = cmd.cleanup_jobs()

        assert skipped == 10
        assert deleted == 0
        mock_pre.assert_not_called()
