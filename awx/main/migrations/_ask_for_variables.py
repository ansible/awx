def migrate_credential(apps, schema_editor):
    '''If credential is not currently present, set ask_for_credential_on_launch
    equal to True, and otherwise leave it as the default False value.
    '''
    JobTemplate = apps.get_model('main', 'JobTemplate')
    for jt in JobTemplate.objects.iterator():
        if jt.credential is None:
            jt.ask_credential_on_launch = True
            jt.save()
