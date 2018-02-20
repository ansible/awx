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


def migrate_workflow_cred(app, schema_editor):
    WorkflowJobTemplateNode = app.get_model('main', 'WorkflowJobTemplateNode')
    WorkflowJobNode = app.get_model('main', 'WorkflowJobNode')

    for cls in (WorkflowJobNode, WorkflowJobTemplateNode):
        for node in cls.objects.iterator():
            if node.credential:
                node.credentials.add(j.credential)


def migrate_workflow_cred_reverse(app, schema_editor):
    WorkflowJobTemplateNode = app.get_model('main', 'WorkflowJobTemplateNode')
    WorkflowJobNode = app.get_model('main', 'WorkflowJobNode')

    for cls in (WorkflowJobNode, WorkflowJobTemplateNode):
        for node in cls.objects.iterator():
            cred = node.credentials.first()
            if cred:
                node.credential = cred
                node.save()


def migrate_inventory_source_cred(app, schema_editor):
    InventoryUpdate = app.get_model('main', 'InventoryUpdate')
    InventorySource = app.get_model('main', 'InventorySource')

    for cls in (InventoryUpdate, InventorySource):
        for obj in cls.objects.iterator():
            if obj.credential:
                obj.credentials.add(obj.credential)


def migrate_inventory_source_cred_reverse(app, schema_editor):
    InventoryUpdate = app.get_model('main', 'InventoryUpdate')
    InventorySource = app.get_model('main', 'InventorySource')

    for cls in (InventoryUpdate, InventorySource):
        for obj in cls.objects.iterator():
            cred = obj.credentials.first()
            if cred:
                obj.credential = cred
                obj.save()
