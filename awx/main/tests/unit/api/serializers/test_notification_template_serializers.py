# -*- coding: utf-8 -*-
import pytest
from unittest import mock

from rest_framework.serializers import ValidationError

from awx.api.serializers import NotificationTemplateSerializer
from awx.main.models.notifications import NotificationTemplate


class StubNotificationTemplate:
    notification_type = 'email'


class TestNotificationTemplateSerializer:
    @pytest.mark.parametrize(
        'valid_messages',
        [
            None,
            {'started': None},
            {'started': {'message': None}},
            {'started': {'message': 'valid'}},
            {'started': {'body': 'valid'}},
            {'started': {'message': 'valid', 'body': 'valid'}},
            {'started': None, 'success': None, 'error': None},
            {'started': {'message': None, 'body': None}, 'success': {'message': None, 'body': None}, 'error': {'message': None, 'body': None}},
            {
                'started': {'message': '{{ job.id }}', 'body': '{{ job.status }}'},
                'success': {'message': None, 'body': '{{ job_friendly_name }}'},
                'error': {'message': '{{ url }}', 'body': None},
            },
            {'started': {'body': '{{ job_metadata }}'}},
            {'started': {'body': '{{ job.summary_fields.inventory.total_hosts }}'}},
            {'started': {'body': 'Iñtërnâtiônàlizætiøn'}},
            {
                'workflow_approval': {
                    'running': {'message': 'running'},
                    'approved': None,
                    'timed_out': {'message': 'timed out'},
                    'denied': {'body': 'denied'},
                }
            },
        ],
    )
    def test_valid_messages(self, valid_messages):
        serializer = NotificationTemplateSerializer()
        serializer.instance = StubNotificationTemplate()
        serializer.validate_messages(valid_messages)

    @pytest.mark.parametrize(
        'invalid_messages',
        [
            1,
            [],
            '',
            {'invalid_event': ''},
            {'started': 'should_be_dict'},
            {'started': {'bad_message_type': ''}},
            {'started': {'message': 1}},
            {'started': {'message': []}},
            {'started': {'message': {}}},
            {'started': {'message': '{{ unclosed_braces'}},
            {'started': {'message': '{{ undefined }}'}},
            {'started': {'message': '{{ job.undefined }}'}},
            {'started': {'message': '{{ job.id | bad_filter }}'}},
            {'started': {'message': '{{ job.__class__ }}'}},
            {'started': {'message': 'Newlines \n not allowed\n'}},
            {'workflow_approval': {'invalid_subevent': {}}},
            {'workflow_approval': {'running': 'should_be_dict'}},
        ],
    )
    def test_invalid__messages(self, invalid_messages):
        serializer = NotificationTemplateSerializer()
        serializer.instance = StubNotificationTemplate()
        with pytest.raises(ValidationError):
            serializer.validate_messages(invalid_messages)


class TestNotificationTemplateTypeSwitch:
    """Tests for the guard that strips stale config keys on notification_type change."""

    def _make_serializer(self, instance_type, instance_config):
        instance = mock.Mock(spec=NotificationTemplate)
        instance.notification_type = instance_type
        instance.notification_configuration = instance_config
        view = mock.Mock()
        view.kwargs = {}
        serializer = NotificationTemplateSerializer(instance=instance, context={'view': view})
        return serializer

    def test_type_switch_strips_stale_keys(self):
        """Switching from slack to rocketchat must strip the encrypted 'token'
        and 'channels' keys that are not valid for rocketchat."""
        instance_config = {
            'token': '$encrypted$fernet-ciphertext-here',
            'channels': ['#alerts'],
        }
        serializer = self._make_serializer('slack', instance_config)

        attrs = {
            'notification_type': 'rocketchat',
            'notification_configuration': {
                'token': '$encrypted$fernet-ciphertext-here',
                'channels': ['#alerts'],
                'rocketchat_url': 'https://chat.example.com',
                'rocketchat_no_verify_ssl': False,
            },
        }

        result = serializer.validate(attrs)
        config = result['notification_configuration']
        assert 'token' not in config
        assert 'channels' not in config
        assert config['rocketchat_url'] == 'https://chat.example.com'

    def test_type_switch_copies_instance_config_when_not_in_attrs(self):
        """If the PATCH only changes notification_type (no new config provided),
        the existing config should be copied and stale keys stripped.
        Validation still raises for missing required rocketchat fields, but the
        stale slack keys must have been removed from the copied config."""
        instance_config = {
            'token': '$encrypted$fernet-ciphertext-here',
            'channels': ['#alerts'],
        }
        serializer = self._make_serializer('slack', instance_config)

        attrs = {
            'notification_type': 'rocketchat',
        }

        with pytest.raises(ValidationError):
            serializer.validate(attrs)
        config = attrs.get('notification_configuration', {})
        assert 'token' not in config
        assert 'channels' not in config

    def test_same_type_update_preserves_config(self):
        """Updating a slack NT without changing type must keep its token field."""
        from awx.api.views import NotificationTemplateDetail

        instance = mock.Mock(spec=NotificationTemplate)
        instance.notification_type = 'slack'
        instance.notification_configuration = {
            'token': '$encrypted$fernet-ciphertext-here',
            'channels': ['#alerts'],
        }

        view = mock.Mock(spec=NotificationTemplateDetail)
        view.kwargs = {'pk': 1}
        view.get_object.return_value = instance
        serializer = NotificationTemplateSerializer(instance=instance, context={'view': view})

        attrs = {
            'notification_type': 'slack',
            'notification_configuration': {
                'token': '$encrypted$',
                'channels': ['#alerts'],
            },
        }

        result = serializer.validate(attrs)
        config = result['notification_configuration']
        assert 'token' in config
        assert 'channels' in config


class TestRawEncryptedValueRejection:
    """Tests for the guard that rejects raw $encrypted$ ciphertext in password fields."""

    def test_rejects_raw_encrypted_ciphertext_in_password_field(self):
        """A password field containing '$encrypted$<actual-ciphertext>' must be rejected."""
        view = mock.Mock()
        view.kwargs = {}
        serializer = NotificationTemplateSerializer(context={'view': view})

        attrs = {
            'notification_type': 'webhook',
            'notification_configuration': {
                'url': 'https://example.com/hook',
                'http_method': 'POST',
                'disable_ssl_verification': False,
                'username': 'user',
                'password': '$encrypted$AQAQA-leaked-ciphertext',
                'headers': {},
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate(attrs)
        errors = exc_info.value.detail
        assert any('Raw encrypted values are not allowed' in str(e) for e in errors)

    def test_allows_encrypted_sentinel_in_password_field(self):
        """The sentinel '$encrypted$' (with no trailing ciphertext) must still
        be allowed — it signals 'keep existing password'."""
        from awx.api.views import NotificationTemplateDetail

        instance = mock.Mock(spec=NotificationTemplate)
        instance.notification_type = 'webhook'
        instance.notification_configuration = {
            'url': 'https://example.com/hook',
            'http_method': 'POST',
            'disable_ssl_verification': False,
            'username': 'user',
            'password': '$encrypted$real-stored-value',
            'headers': {},
        }

        view = mock.Mock(spec=NotificationTemplateDetail)
        view.kwargs = {'pk': 1}
        view.get_object.return_value = instance
        serializer = NotificationTemplateSerializer(instance=instance, context={'view': view})

        attrs = {
            'notification_type': 'webhook',
            'notification_configuration': {
                'url': 'https://example.com/hook',
                'http_method': 'POST',
                'disable_ssl_verification': False,
                'username': 'user',
                'password': '$encrypted$',
                'headers': {},
            },
        }
        result = serializer.validate(attrs)
        assert result['notification_configuration']['password'] == (instance.notification_configuration['password'])

    def test_allows_plaintext_password(self):
        """A normal plaintext password must still be accepted."""
        view = mock.Mock()
        view.kwargs = {}
        serializer = NotificationTemplateSerializer(context={'view': view})

        attrs = {
            'notification_type': 'webhook',
            'notification_configuration': {
                'url': 'https://example.com/hook',
                'http_method': 'POST',
                'disable_ssl_verification': False,
                'username': 'user',
                'password': 'my-secret-password',
                'headers': {},
            },
        }
        from awx.api.serializers import BaseSerializer

        with mock.patch.object(BaseSerializer, 'validate', return_value=attrs):
            result = serializer.validate(attrs)
        assert result['notification_configuration']['password'] == 'my-secret-password'


class TestDisplayNotificationConfiguration:
    """Tests for masking encrypted values in display_notification_configuration."""

    def test_masks_stale_encrypted_key_not_in_current_type(self):
        """A stale encrypted key left from a previous type must be masked to
        '$encrypted$' — before the fix it would leak the full ciphertext."""
        nt = NotificationTemplate.__new__(NotificationTemplate)
        nt.notification_type = 'rocketchat'
        nt.notification_configuration = {
            'rocketchat_url': 'https://chat.example.com',
            'rocketchat_no_verify_ssl': False,
            'token': '$encrypted$AQAQA-leaked-ciphertext',
        }
        display = nt.display_notification_configuration()
        assert display['token'] == '$encrypted$'
        assert display['rocketchat_url'] == 'https://chat.example.com'

    def test_masks_current_type_password_field(self):
        """An encrypted password field belonging to the current type is masked."""
        nt = NotificationTemplate.__new__(NotificationTemplate)
        nt.notification_type = 'webhook'
        nt.notification_configuration = {
            'url': 'https://example.com/hook',
            'http_method': 'POST',
            'disable_ssl_verification': False,
            'username': 'user',
            'password': '$encrypted$some-encrypted-value',
            'headers': {},
        }
        display = nt.display_notification_configuration()
        assert display['password'] == '$encrypted$'
        assert display['url'] == 'https://example.com/hook'

    def test_does_not_mask_non_encrypted_values(self):
        """Non-encrypted values must pass through unmodified."""
        nt = NotificationTemplate.__new__(NotificationTemplate)
        nt.notification_type = 'slack'
        nt.notification_configuration = {
            'token': 'plaintext-token',
            'channels': ['#alerts'],
        }
        display = nt.display_notification_configuration()
        assert display['token'] == 'plaintext-token'
        assert display['channels'] == ['#alerts']


class TestModelSaveStaleKeyCleanup:
    """Tests for the save() guard that removes stale encrypted keys."""

    def test_save_removes_stale_encrypted_key(self):
        """During save, a config key not in the current type's init_parameters
        whose value starts with '$encrypted$' must be deleted."""
        nt = NotificationTemplate.__new__(NotificationTemplate)
        nt.pk = 1
        nt.id = 1
        nt.notification_type = 'rocketchat'
        nt.notification_configuration = {
            'rocketchat_url': 'https://chat.example.com',
            'rocketchat_no_verify_ssl': False,
            'token': '$encrypted$AQAQA-stale-ciphertext',
        }
        nt.messages = None

        old_nt = mock.Mock(spec=NotificationTemplate)
        old_nt.messages = None

        with mock.patch.object(NotificationTemplate.objects, 'get', return_value=old_nt), mock.patch(
            'awx.main.models.notifications.encrypt_field'
        ), mock.patch.object(type(nt).__mro__[1], 'save', create=True):
            nt.save()

        assert 'token' not in nt.notification_configuration
        assert nt.notification_configuration['rocketchat_url'] == 'https://chat.example.com'

    def test_save_keeps_non_encrypted_stale_key(self):
        """A stale key whose value does NOT start with '$encrypted$'
        should not be removed — only encrypted stale keys are dangerous."""
        nt = NotificationTemplate.__new__(NotificationTemplate)
        nt.pk = 1
        nt.id = 1
        nt.notification_type = 'rocketchat'
        nt.notification_configuration = {
            'rocketchat_url': 'https://chat.example.com',
            'rocketchat_no_verify_ssl': False,
            'channels': ['#alerts'],
        }
        nt.messages = None

        old_nt = mock.Mock(spec=NotificationTemplate)
        old_nt.messages = None

        with mock.patch.object(NotificationTemplate.objects, 'get', return_value=old_nt), mock.patch(
            'awx.main.models.notifications.encrypt_field'
        ), mock.patch.object(type(nt).__mro__[1], 'save', create=True):
            nt.save()

        assert nt.notification_configuration['channels'] == ['#alerts']
