def migrate_to_multi_cred(app, schema_editor):
    Job = app.get_model('main', 'Job')
    JobTemplate = app.get_model('main', 'JobTemplate')

    for cls in (Job, JobTemplate):
        for j in cls.objects.iterator():
            if j.credential:
                j.credentials.add(j.credential)
            if j.vault_credential:
                j.credentials.add(j.vault_credential)
            for cred in j.extra_credentials.all():
                j.credentials.add(cred)
