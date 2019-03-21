import logging

from django.utils.timezone import now
from django.utils.text import slugify

from awx.main.models.base import PERM_INVENTORY_SCAN, PERM_INVENTORY_DEPLOY
from awx.main import utils


logger = logging.getLogger('awx.main.migrations')


def _create_fact_scan_project(ContentType, Project, org):
    ct = ContentType.objects.get_for_model(Project)
    name = u"Tower Fact Scan - {}".format(org.name if org else "No Organization")
    proj = Project(name=name,
                   scm_url='https://github.com/ansible/awx-facts-playbooks',
                   scm_type='git',
                   scm_update_on_launch=True,
                   scm_update_cache_timeout=86400,
                   organization=org,
                   created=now(),
                   modified=now(),
                   polymorphic_ctype=ct)
    proj.save()

    slug_name = slugify(str(name)).replace(u'-', u'_')
    proj.local_path = u'_%d__%s' % (int(proj.pk), slug_name)

    proj.save()
    return proj


def _create_fact_scan_projects(ContentType, Project, orgs):
    return {org.id : _create_fact_scan_project(ContentType, Project, org) for org in orgs}


def _get_tower_scan_job_templates(JobTemplate):
    return JobTemplate.objects.filter(job_type=PERM_INVENTORY_SCAN, project__isnull=True) \
                              .prefetch_related('inventory__organization')


def _get_orgs(Organization, job_template_ids):
    return Organization.objects.filter(inventories__jobtemplates__in=job_template_ids).distinct()


def _migrate_scan_job_templates(apps):
    JobTemplate = apps.get_model('main', 'JobTemplate')
    Organization = apps.get_model('main', 'Organization')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Project = apps.get_model('main', 'Project')

    project_no_org = None

    # A scan job template with a custom project will retain the custom project.
    JobTemplate.objects.filter(job_type=PERM_INVENTORY_SCAN, project__isnull=False).update(use_fact_cache=True, job_type=PERM_INVENTORY_DEPLOY)

    # Scan jobs templates using Tower's default scan playbook will now point at
    # the same playbook but in a github repo.
    jts = _get_tower_scan_job_templates(JobTemplate)
    if jts.count() == 0:
        return

    orgs = _get_orgs(Organization, jts.values_list('id'))
    if orgs.count() == 0:
        return

    org_proj_map = _create_fact_scan_projects(ContentType, Project, orgs)
    for jt in jts:
        if jt.inventory and jt.inventory.organization:
            jt.project_id = org_proj_map[jt.inventory.organization.id].id
        # Job Templates without an Organization; through related Inventory
        else:
            if not project_no_org:
                project_no_org = _create_fact_scan_project(ContentType, Project, None)
            jt.project_id = project_no_org.id
        jt.job_type = PERM_INVENTORY_DEPLOY
        jt.playbook = "scan_facts.yml"
        jt.use_fact_cache = True
        jt.save()


def migrate_scan_job_templates(apps, schema_editor):
    _migrate_scan_job_templates(apps)


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
