from unittest import mock

import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from ansible_base.lib.serializers.mixins import CleanTextMixin

from awx.api.serializers import (
    BulkJobNodeSerializer,
    CopySerializer,
    CredentialSerializer,
    ExecutionEnvironmentSerializer,
    HostSerializer,
)


UNSAFE_INPUT = '<script>x</script>'


def _passthrough_validate(self, attrs):
    return attrs


class TestCopySerializerValidate:
    def test_rejects_copy_with_the_same_name(self):
        original = mock.Mock()
        original.name = 'keep-me'
        view = mock.Mock()
        view.get_object.return_value = original
        serializer = CopySerializer(context={'view': view})

        with pytest.raises(ValidationError) as exc:
            serializer.validate({'name': 'keep-me'})

        assert 'already named' in str(exc.value.detail)


@pytest.mark.django_db
class TestHostSerializerPortParsing:
    def test_extracts_inline_ssh_port(self):
        serializer = HostSerializer()
        assert serializer._get_host_port_from_name('web.example.com:2222') == ('web.example.com', 2222)

    @pytest.mark.parametrize('name', ['web.example.com:0', 'web.example.com:65536', 'web.example.com:notaport'])
    def test_rejects_invalid_inline_port(self, name):
        serializer = HostSerializer()
        with pytest.raises(ValidationError):
            serializer._get_host_port_from_name(name)

    def test_validate_moves_port_into_ansible_ssh_port(self):
        serializer = HostSerializer()
        with mock.patch.object(CleanTextMixin, 'validate', _passthrough_validate):
            attrs = serializer.validate({'name': 'web.example.com:2222'})

        assert attrs['name'] == 'web.example.com'
        assert '"ansible_ssh_port": 2222' in attrs['variables']


@pytest.mark.django_db
class TestCredentialSerializerValidate:
    def test_rejects_updates_to_managed_credentials(self):
        serializer = CredentialSerializer()
        serializer.instance = mock.Mock(managed=True)

        with pytest.raises(PermissionDenied):
            serializer.validate({'name': 'nope'})

    def test_fail_closed_excludes_inputs_when_type_is_unknown(self):
        serializer = CredentialSerializer()
        with mock.patch.object(CleanTextMixin, 'validate', _passthrough_validate):
            serializer.validate({'name': 'no-type', 'inputs': {'username': UNSAFE_INPUT}})

        assert 'inputs' in serializer.excluded_fields


@pytest.mark.django_db
class TestBulkJobNodeCleanText:
    def test_run_clean_text_validation_raises_when_enforced(self):
        serializer = BulkJobNodeSerializer()
        with mock.patch('awx.api.serializers.get_setting', return_value=True):
            with pytest.raises(ValidationError) as exc:
                serializer._run_clean_text_validation({'limit': UNSAFE_INPUT})

        assert 'limit' in exc.value.detail


@pytest.mark.django_db
class TestExecutionEnvironmentSerializerValidate:
    def test_rejects_non_registry_credentials(self):
        serializer = ExecutionEnvironmentSerializer()
        with pytest.raises(ValidationError):
            serializer.validate_credential(mock.Mock(kind='ssh'))

    def test_accepts_registry_credentials(self):
        credential = mock.Mock(kind='registry')
        assert ExecutionEnvironmentSerializer().validate_credential(credential) is credential

    def test_rejects_organization_change(self):
        serializer = ExecutionEnvironmentSerializer()
        serializer.instance = mock.Mock(organization_id=1)

        with pytest.raises(ValidationError) as exc:
            serializer.validate({'organization': mock.Mock(pk=2)})

        assert 'organization' in exc.value.detail

    def test_allows_same_organization(self):
        serializer = ExecutionEnvironmentSerializer()
        serializer.instance = mock.Mock(organization_id=1)
        org = mock.Mock(pk=1)
        with mock.patch.object(CleanTextMixin, 'validate', _passthrough_validate):
            attrs = serializer.validate({'organization': org})

        assert attrs['organization'] is org
