import pytest
import mock

from django.apps import apps

from awx.main.models import (
    NotificationTemplate,
    Credential,
)
from awx.main.models.credential import ssh

from awx.conf.migrations._reencrypt import encrypt_field
from awx.main.migrations._reencrypt import (
    _notification_templates,
    _credentials,
)

from awx.main.utils import decrypt_field


@pytest.mark.django_db
def test_notification_template_migration():
    with mock.patch('awx.main.models.notifications.encrypt_field', encrypt_field):
        nt = NotificationTemplate.objects.create(notification_type='slack', notification_configuration=dict(token='test'))


    assert nt.notification_configuration['token'].startswith('$encrypted$AES$')

    _notification_templates(apps)
    nt.refresh_from_db()

    assert nt.notification_configuration['token'].startswith('$encrypted$AESCBC$')
    assert decrypt_field(nt, 'notification_configuration', subfield='token') == 'test'


@pytest.mark.django_db
def test_credential_migration():
    with mock.patch('awx.main.models.credential.encrypt_field', encrypt_field):
        cred_type = ssh()
        cred_type.save()

        cred = Credential.objects.create(credential_type=cred_type, inputs=dict(password='test'))

    _credentials(apps)
    cred.refresh_from_db()

    assert cred.password.startswith('$encrypted$AESCBC$')
    assert decrypt_field(cred, 'password') == 'test'
