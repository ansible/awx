import json

from cryptography.fernet import InvalidToken
from django.test.utils import override_settings
from django.conf import settings
import pytest

from awx.main import models
from awx.conf.models import Setting
from awx.main.management.commands import regenerate_secret_key
from awx.main.utils.encryption import encrypt_field, decrypt_field, encrypt_value


PREFIX = '$encrypted$UTF8$AESCBC$'


@pytest.mark.django_db
class TestKeyRegeneration:

    def test_encrypted_ssh_password(self, credential):
        # test basic decryption
        assert credential.inputs['password'].startswith(PREFIX)
        assert credential.get_input('password') == 'secret'

        # re-key the credential
        new_key = regenerate_secret_key.Command().handle()
        new_cred = models.Credential.objects.get(pk=credential.pk)
        assert credential.inputs['password'] != new_cred.inputs['password']

        # verify that the old SECRET_KEY doesn't work
        with pytest.raises(InvalidToken):
            new_cred.get_input('password')

        # verify that the new SECRET_KEY *does* work
        with override_settings(SECRET_KEY=new_key):
            assert new_cred.get_input('password') == 'secret'

    def test_encrypted_setting_values(self):
        # test basic decryption
        settings.REDHAT_PASSWORD = 'sensitive'
        s = Setting.objects.filter(key='REDHAT_PASSWORD').first()
        assert s.value.startswith(PREFIX)
        assert settings.REDHAT_PASSWORD == 'sensitive'

        # re-key the setting value
        new_key = regenerate_secret_key.Command().handle()
        new_setting = Setting.objects.filter(key='REDHAT_PASSWORD').first()
        assert s.value != new_setting.value

        # wipe out the local cache so the value is pulled from the DB again
        settings.cache.delete('REDHAT_PASSWORD')

        # verify that the old SECRET_KEY doesn't work
        with pytest.raises(InvalidToken):
            settings.REDHAT_PASSWORD

        # verify that the new SECRET_KEY *does* work
        with override_settings(SECRET_KEY=new_key):
            assert settings.REDHAT_PASSWORD == 'sensitive'

    def test_encrypted_notification_secrets(self, notification_template_with_encrypt):
        # test basic decryption
        nt = notification_template_with_encrypt
        nc = nt.notification_configuration
        assert nc['token'].startswith(PREFIX)

        Slack = nt.CLASS_FOR_NOTIFICATION_TYPE[nt.notification_type]

        class TestBackend(Slack):

            def __init__(self, *args, **kw):
                assert kw['token'] == 'token'

            def send_messages(self, messages):
                pass

        nt.CLASS_FOR_NOTIFICATION_TYPE['test'] = TestBackend
        nt.notification_type = 'test'
        nt.send('Subject', 'Body')

        # re-key the notification config
        new_key = regenerate_secret_key.Command().handle()
        new_nt = models.NotificationTemplate.objects.get(pk=nt.pk)
        assert nt.notification_configuration['token'] != new_nt.notification_configuration['token']

        # verify that the old SECRET_KEY doesn't work
        with pytest.raises(InvalidToken):
            new_nt.CLASS_FOR_NOTIFICATION_TYPE['test'] = TestBackend
            new_nt.notification_type = 'test'
            new_nt.send('Subject', 'Body')

        # verify that the new SECRET_KEY *does* work
        with override_settings(SECRET_KEY=new_key):
            new_nt.send('Subject', 'Body')

    def test_job_start_args(self, job_factory):
        # test basic decryption
        job = job_factory()
        job.start_args = json.dumps({'foo': 'bar'})
        job.start_args = encrypt_field(job, field_name='start_args')
        job.save()
        assert job.start_args.startswith(PREFIX)

        # re-key the start_args
        new_key = regenerate_secret_key.Command().handle()
        new_job = models.Job.objects.get(pk=job.pk)
        assert new_job.start_args != job.start_args

        # verify that the old SECRET_KEY doesn't work
        with pytest.raises(InvalidToken):
            decrypt_field(new_job, field_name='start_args')

        # verify that the new SECRET_KEY *does* work
        with override_settings(SECRET_KEY=new_key):
            assert json.loads(
                decrypt_field(new_job, field_name='start_args')
            ) == {'foo': 'bar'}

    @pytest.mark.parametrize('cls', ('JobTemplate', 'WorkflowJobTemplate'))
    def test_survey_spec(self, inventory, project, survey_spec_factory, cls):
        params = {}
        if cls == 'JobTemplate':
            params['inventory'] = inventory
            params['project'] = project
        # test basic decryption
        jt = getattr(models, cls).objects.create(
            name='Example Template',
            survey_spec=survey_spec_factory([{
                'variable': 'secret_key',
                'default': encrypt_value('donttell', pk=None),
                'type': 'password'
            }]),
            survey_enabled=True,
            **params
        )
        job = jt.create_unified_job()
        assert jt.survey_spec['spec'][0]['default'].startswith(PREFIX)
        assert job.survey_passwords == {'secret_key': '$encrypted$'}
        assert json.loads(job.decrypted_extra_vars())['secret_key'] == 'donttell'

        # re-key the extra_vars
        new_key = regenerate_secret_key.Command().handle()
        new_job = models.UnifiedJob.objects.get(pk=job.pk)
        assert new_job.extra_vars != job.extra_vars

        # verify that the old SECRET_KEY doesn't work
        with pytest.raises(InvalidToken):
            new_job.decrypted_extra_vars()

        # verify that the new SECRET_KEY *does* work
        with override_settings(SECRET_KEY=new_key):
            assert json.loads(
                new_job.decrypted_extra_vars()
            )['secret_key'] == 'donttell'

    def test_oauth2_application_client_secret(self, oauth_application):
        # test basic decryption
        secret = oauth_application.client_secret
        assert len(secret) == 128

        # re-key the client_secret
        new_key = regenerate_secret_key.Command().handle()

        # verify that the old SECRET_KEY doesn't work
        with pytest.raises(InvalidToken):
            models.OAuth2Application.objects.get(
                pk=oauth_application.pk
            ).client_secret

        # verify that the new SECRET_KEY *does* work
        with override_settings(SECRET_KEY=new_key):
            assert models.OAuth2Application.objects.get(
                pk=oauth_application.pk
            ).client_secret == secret
