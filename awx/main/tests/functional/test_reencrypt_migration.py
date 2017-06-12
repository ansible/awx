import json
import pytest
import mock

from django.apps import apps

from awx.main.models import (
    UnifiedJob,
    NotificationTemplate,
    Credential,
)
from awx.main.models.credential import ssh

from awx.conf.migrations._reencrypt import encrypt_field
from awx.main.migrations._reencrypt import (
    _notification_templates,
    _credentials,
    _unified_jobs,
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

    # This is here for a side-effect.
    # Exception if the encryption type of AESCBC is not properly skipped, ensures
    # our `startswith` calls don't have typos
    _notification_templates(apps)


@pytest.mark.django_db
def test_credential_migration():
    with mock.patch('awx.main.models.credential.encrypt_field', encrypt_field):
        cred_type = ssh()
        cred_type.save()

        cred = Credential.objects.create(credential_type=cred_type, inputs=dict(password='test'))

    assert cred.password.startswith('$encrypted$AES$')

    _credentials(apps)
    cred.refresh_from_db()

    assert cred.password.startswith('$encrypted$AESCBC$')
    assert decrypt_field(cred, 'password') == 'test'

    # This is here for a side-effect.
    # Exception if the encryption type of AESCBC is not properly skipped, ensures
    # our `startswith` calls don't have typos
    _credentials(apps)


@pytest.mark.django_db
def test_unified_job_migration():
    with mock.patch('awx.main.models.base.encrypt_field', encrypt_field):
        uj = UnifiedJob.objects.create(launch_type='manual', start_args=json.dumps({'test':'value'}))

    assert uj.start_args.startswith('$encrypted$AES$')

    _unified_jobs(apps)
    uj.refresh_from_db()

    assert uj.start_args.startswith('$encrypted$AESCBC$')
    assert json.loads(decrypt_field(uj, 'start_args')) == {'test':'value'}

    # This is here for a side-effect.
    # Exception if the encryption type of AESCBC is not properly skipped, ensures
    # our `startswith` calls don't have typos
    _unified_jobs(apps)
