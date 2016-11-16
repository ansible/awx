from awx.main import signals


class TestCleanupDetachedLabels:
    def test_cleanup_detached_labels_on_deleted_parent(self, mocker):
        mock_labels = [mocker.MagicMock(), mocker.MagicMock()]
        mock_instance = mocker.MagicMock()
        mock_instance.labels.all = mocker.MagicMock()
        mock_instance.labels.all.return_value = mock_labels
        mock_labels[0].is_candidate_for_detach.return_value = True
        mock_labels[1].is_candidate_for_detach.return_value = False

        signals.cleanup_detached_labels_on_deleted_parent(None, mock_instance)

        mock_labels[0].is_candidate_for_detach.assert_called_with()
        mock_labels[1].is_candidate_for_detach.assert_called_with()
        mock_labels[0].delete.assert_called_with()
        mock_labels[1].delete.assert_not_called()
