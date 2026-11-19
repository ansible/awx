import pytest
from unittest import mock

from rest_framework import serializers as drf_serializers

from awx.api.serializers import ProjectOptionsSerializer


@mock.patch('awx.api.serializers.BaseSerializer.validate', lambda self, attrs: attrs)
class TestProjectOptionsSerializerDashUrlGuard:
    """The scm_url field must reject values that begin with a dash
    (after whitespace stripping) to prevent argument injection."""

    @pytest.mark.parametrize(
        'scm_url',
        [
            '--upload-pack=id>&2;echo:x',
            '-malicious',
            '  --upload-pack=id>&2;echo:x',
        ],
    )
    def test_rejects_dash_prefixed_scm_url(self, scm_url):
        serializer = ProjectOptionsSerializer()
        serializer.instance = None
        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate({'scm_type': 'git', 'scm_url': scm_url})
        assert 'scm_url' in exc_info.value.detail

    @pytest.mark.parametrize(
        'scm_url',
        [
            'https://example.com/repo.git',
            'git://example.com/foo.git',
        ],
    )
    def test_permits_normal_scm_url(self, scm_url):
        serializer = ProjectOptionsSerializer()
        serializer.instance = None
        result = serializer.validate({'scm_type': 'git', 'scm_url': scm_url})
        assert result['scm_url'] == scm_url

    def test_permits_absent_scm_url(self):
        serializer = ProjectOptionsSerializer()
        serializer.instance = None
        result = serializer.validate({'scm_type': 'git'})
        assert 'scm_url' not in result or result.get('scm_url') is None
