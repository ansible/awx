import pytest

from awx.main import signals


class TestExtractImageRepo:
    @pytest.mark.parametrize(
        'image_ref,expected',
        [
            ('quay.io/ansible/awx-ee:latest', 'quay.io/ansible/awx-ee'),
            ('registry.io/repo:v1.2.3', 'registry.io/repo'),
            ('repo:tag', 'repo'),
            ('quay.io/ansible/awx-ee@sha256:abc123def456', 'quay.io/ansible/awx-ee'),
            ('registry.io/repo@sha256:xyz789', 'registry.io/repo'),
            ('quay.io/ansible/awx-ee', 'quay.io/ansible/awx-ee'),
            ('registry.io/repo', 'registry.io/repo'),
            ('repo', 'repo'),
            ('localhost:5000/repo:tag', 'localhost:5000/repo'),
            ('registry.example.com:443/path/to/repo:latest', 'registry.example.com:443/path/to/repo'),
            (None, None),
            ('', None),
        ],
    )
    def test_extract_image_repo(self, image_ref, expected):
        assert signals._extract_image_repo(image_ref) == expected


class TestDifferentRefForms:
    def test_tag_vs_digest(self):
        assert signals._different_ref_forms('repo:latest', 'repo@sha256:abc') is True

    def test_digest_vs_tag(self):
        assert signals._different_ref_forms('repo@sha256:abc', 'repo:latest') is True

    def test_both_tags(self):
        assert signals._different_ref_forms('repo:v1', 'repo:v2') is False

    def test_both_digests(self):
        assert signals._different_ref_forms('repo@sha256:aaa', 'repo@sha256:bbb') is False

    def test_bare_vs_digest(self):
        assert signals._different_ref_forms('repo', 'repo@sha256:abc') is True


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
