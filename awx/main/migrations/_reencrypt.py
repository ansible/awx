from awx.conf.migrations._reencrypt import decrypt_field


__all__ = ['replace_aesecb_fernet']


def replace_aesecb_fernet(apps, schema_editor):
    _notification_templates(apps)
    _credentials(apps)


def _notification_templates(apps):
    NotificationTemplate = apps.get_model('main', 'NotificationTemplate')
    for nt in NotificationTemplate.objects.all():
        for field in filter(lambda x: nt.notification_class.init_parameters[x]['type'] == "password",
                            nt.notification_class.init_parameters):
            try:
                value = decrypt_field(nt, 'notification_configuration', subfield=field)
                nt.notification_configuration[field] = value
            except ValueError:
                continue
        nt.save()


def _credentials(apps):
    Credential = apps.get_model('main', 'Credential')
    for credential in Credential.objects.all():
        for field_name, value in credential.inputs.items():
            if field_name in credential.credential_type.secret_fields:
                try:
                    value = decrypt_field(credential, field_name)
                    credential.inputs[field_name] = value
                except ValueError:
                    continue
        credential.save()
