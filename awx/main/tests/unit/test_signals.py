import pytest
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


class TestExtractImageRepo:
    """Tests for _extract_image_repo helper function (AAP-89067)"""

    @pytest.mark.parametrize(
        'image_ref,expected',
        [
            # Tag-based references
            ('quay.io/ansible/awx-ee:latest', 'quay.io/ansible/awx-ee'),
            ('registry.io/repo:v1.2.3', 'registry.io/repo'),
            ('repo:tag', 'repo'),
            # Digest-based references
            ('quay.io/ansible/awx-ee@sha256:abc123def456', 'quay.io/ansible/awx-ee'),
            ('registry.io/repo@sha256:xyz789', 'registry.io/repo'),
            # No tag or digest
            ('quay.io/ansible/awx-ee', 'quay.io/ansible/awx-ee'),
            ('registry.io/repo', 'registry.io/repo'),
            ('repo', 'repo'),
            # Registry with port (should preserve)
            ('localhost:5000/repo:tag', 'localhost:5000/repo'),
            ('registry.example.com:443/path/to/repo:latest', 'registry.example.com:443/path/to/repo'),
            # Edge cases
            (None, None),
            ('', None),
        ],
    )
    def test_extract_image_repo(self, image_ref, expected):
        result = signals._extract_image_repo(image_ref)
        assert result == expected

    def test_extract_image_repo_preserves_path_with_colon(self):
        # If colon is part of path, not a tag separator
        result = signals._extract_image_repo('registry.io/path:with:colons/repo')
        # This should not strip, as the part after : contains /
        assert result == 'registry.io/path:with:colons/repo'
