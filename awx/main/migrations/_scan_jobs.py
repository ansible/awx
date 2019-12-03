import logging


logger = logging.getLogger('awx.main.migrations')


def remove_scan_type_nodes(apps, schema_editor):
    WorkflowJobTemplateNode = apps.get_model('main', 'WorkflowJobTemplateNode')
    WorkflowJobNode = apps.get_model('main', 'WorkflowJobNode')

    for cls in (WorkflowJobNode, WorkflowJobTemplateNode):
        for node in cls.objects.iterator():
            prompts = node.char_prompts
            if prompts.get('job_type', None) == 'scan':
                log_text = '{} set job_type to scan, which was deprecated in 3.2, removing.'.format(cls)
                if cls == WorkflowJobNode:
                    logger.info(log_text)
                else:
                    logger.debug(log_text)
                prompts.pop('job_type')
                node.char_prompts = prompts
                node.save()


def remove_legacy_fact_cleanup(apps, schema_editor):
    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    for job in SystemJobTemplate.objects.filter(job_type='cleanup_facts').all():
        for sched in job.schedules.all():
            sched.delete()
        job.delete()
