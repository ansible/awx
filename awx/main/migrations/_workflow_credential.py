def migrate_workflow_cred(app, schema_editor):
    WorkflowJobTemplateNode = app.get_model('main', 'WorkflowJobTemplateNode')
    WorkflowJobNode = app.get_model('main', 'WorkflowJobNode')

    for cls in (WorkflowJobNode, WorkflowJobTemplateNode):
        for j in cls.objects.iterator():
            if j.credential:
                j.credentials.add(j.credential)