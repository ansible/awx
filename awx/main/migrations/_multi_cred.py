import logging


logger = logging.getLogger('awx.main.migrations')


def migrate_to_multi_cred(app, schema_editor):
    Job = app.get_model('main', 'Job')
    JobTemplate = app.get_model('main', 'JobTemplate')

    ct = 0
    for cls in (Job, JobTemplate):
        for j in cls.objects.iterator():
            if j.credential:
                ct += 1
                logger.debug('Migrating cred %s to %s %s multi-cred relation.', j.credential_id, cls, j.id)
                j.credentials.add(j.credential)
            if j.vault_credential:
                ct += 1
                logger.debug('Migrating cred %s to %s %s multi-cred relation.', j.vault_credential_id, cls, j.id)
                j.credentials.add(j.vault_credential)
            for cred in j.extra_credentials.all():
                ct += 1
                logger.debug('Migrating cred %s to %s %s multi-cred relation.', cred.id, cls, j.id)
                j.credentials.add(cred)
    if ct:
        logger.info('Finished migrating %s credentials to multi-cred', ct)


def migrate_back_from_multi_cred(app, schema_editor):
    Job = app.get_model('main', 'Job')
    JobTemplate = app.get_model('main', 'JobTemplate')
    CredentialType = app.get_model('main', 'CredentialType')
    vault_credtype = CredentialType.objects.get(kind='vault')
    ssh_credtype = CredentialType.objects.get(kind='ssh')

    ct = 0
    for cls in (Job, JobTemplate):
        for j in cls.objects.iterator():
            for cred in j.credentials.iterator():
                changed = False
                if cred.credential_type_id == vault_credtype.id:
                    changed = True
                    ct += 1
                    logger.debug('Reverse migrating vault cred %s for %s %s', cred.id, cls, j.id)
                    j.vault_credential = cred
                elif cred.credential_type_id == ssh_credtype.id:
                    changed = True
                    ct += 1
                    logger.debug('Reverse migrating ssh cred %s for %s %s', cred.id, cls, j.id)
                    j.credential = cred
                else:
                    changed = True
                    ct += 1
                    logger.debug('Reverse migrating cloud cred %s for %s %s', cred.id, cls, j.id)
                    j.extra_credentials.add(cred)
                if changed:
                    j.save()
    if ct:
        logger.info('Finished reverse migrating %s credentials from multi-cred', ct)


def migrate_workflow_cred(app, schema_editor):
    WorkflowJobTemplateNode = app.get_model('main', 'WorkflowJobTemplateNode')
    WorkflowJobNode = app.get_model('main', 'WorkflowJobNode')

    ct = 0
    for cls in (WorkflowJobNode, WorkflowJobTemplateNode):
        for node in cls.objects.iterator():
            if node.credential:
                logger.debug('Migrating prompted credential %s for %s %s', node.credential_id, cls, node.id)
                ct += 1
                node.credentials.add(node.credential)
    if ct:
        logger.info('Finished migrating total of %s workflow prompted credentials', ct)


def migrate_workflow_cred_reverse(app, schema_editor):
    WorkflowJobTemplateNode = app.get_model('main', 'WorkflowJobTemplateNode')
    WorkflowJobNode = app.get_model('main', 'WorkflowJobNode')

    ct = 0
    for cls in (WorkflowJobNode, WorkflowJobTemplateNode):
        for node in cls.objects.iterator():
            cred = node.credentials.first()
            if cred:
                node.credential = cred
                logger.debug('Reverse migrating prompted credential %s for %s %s', node.credential_id, cls, node.id)
                ct += 1
                node.save(update_fields=['credential'])
    if ct:
        logger.info('Finished reverse migrating total of %s workflow prompted credentials', ct)


def migrate_inventory_source_cred(app, schema_editor):
    InventoryUpdate = app.get_model('main', 'InventoryUpdate')
    InventorySource = app.get_model('main', 'InventorySource')

    ct = 0
    for cls in (InventoryUpdate, InventorySource):
        for obj in cls.objects.iterator():
            if obj.credential:
                ct += 1
                logger.debug('Migrating credential %s for %s %s', obj.credential_id, cls, obj.id)
                obj.credentials.add(obj.credential)
    if ct:
        logger.info('Finished migrating %s inventory source credentials to multi-cred', ct)


def migrate_inventory_source_cred_reverse(app, schema_editor):
    InventoryUpdate = app.get_model('main', 'InventoryUpdate')
    InventorySource = app.get_model('main', 'InventorySource')

    ct = 0
    for cls in (InventoryUpdate, InventorySource):
        for obj in cls.objects.iterator():
            cred = obj.credentials.first()
            if cred:
                ct += 1
                logger.debug('Reverse migrating credential %s for %s %s', cred.id, cls, obj.id)
                obj.credential = cred
                obj.save()
    if ct:
        logger.info('Finished reverse migrating %s inventory source credentials from multi-cred', ct)
