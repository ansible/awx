from awx.main import utils
from awx.conf.migrations._reencrypt import decrypt_field


__all__ = ['replace_aesecb_fernet']


def replace_aesecb_fernet(apps, schema_editor):
    _notification_templates(apps)
    _credentials(apps)
    _unified_jobs(apps)


def _notification_templates(apps):
    NotificationTemplate = apps.get_model('main', 'NotificationTemplate')
    for nt in NotificationTemplate.objects.all():
        for field in filter(lambda x: nt.notification_class.init_parameters[x]['type'] == "password",
                            nt.notification_class.init_parameters):
            if nt.notification_configuration[field].startswith('$encrypted$AESCBC$'):
                continue
            value = decrypt_field(nt, 'notification_configuration', subfield=field)
            nt.notification_configuration[field] = value
        nt.save()


def _credentials(apps):
    # this monkey-patch is necessary to make the implicit role generation save
    # signal use the correct Role model (the version active at this point in
    # migration, not the one at HEAD)
    orig_current_apps = utils.get_current_apps
    try:
        utils.get_current_apps = lambda: apps
        for credential in apps.get_model('main', 'Credential').objects.all():
            for field_name, value in credential.inputs.items():
                if value.startswith('$encrypted$AES$'):
                    value = decrypt_field(credential, field_name)
                    credential.inputs[field_name] = value
            credential.save()
    finally:
        utils.get_current_apps = orig_current_apps



def _unified_jobs(apps):
    UnifiedJob = apps.get_model('main', 'UnifiedJob')
    for uj in UnifiedJob.objects.all():
        if uj.start_args is not None:
            if uj.start_args.startswith('$encrypted$AESCBC$'):
                continue
            start_args = decrypt_field(uj, 'start_args')
            uj.start_args = start_args
            uj.save()
