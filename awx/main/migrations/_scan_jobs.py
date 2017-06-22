import logging

from awx.main.models.base import PERM_INVENTORY_SCAN, PERM_INVENTORY_DEPLOY

logger = logging.getLogger('awx.main.migrations')


def _create_fact_scan_project(Project, org):
    name = "Tower Fact Scan - {}".format(org.name if org else "No Organization")
    return Project.objects.create(name=name, 
                                  scm_url='https://github.com/ansible/tower-fact-modules',
                                  organization=org)


def _create_fact_scan_projects(Project, orgs):
    return {org.id : _create_fact_scan_project(Project, org) for org in orgs}


def _get_tower_scan_job_templates(JobTemplate):
    return JobTemplate.objects.filter(job_type=PERM_INVENTORY_SCAN, project__isnull=True) \
                              .prefetch_related('inventory__organization')


def _get_orgs(Organization, job_template_ids):
    return Organization.objects.filter(inventories__jobtemplates__in=job_template_ids).distinct()


def _migrate_scan_job_templates(apps):
    Organization = apps.get_model('main', 'Organization')
    Project = apps.get_model('main', 'Project')
    JobTemplate = apps.get_model('main', 'JobTemplate')

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

    org_proj_map = _create_fact_scan_projects(Project, orgs)
    for jt in jts:
        if jt.inventory and jt.inventory.organization:
            jt.project = org_proj_map[jt.inventory.organization.id]
        # Job Templates without an Organization; through related Inventory
        else:
            # TODO: Create a project without an org and connect
            if not project_no_org:
                project_no_org = _create_fact_scan_project(Project, None)
            jt.project = project_no_org
        jt.job_type = PERM_INVENTORY_DEPLOY
        jt.use_fact_cache = True
        jt.save()


def migrate_scan_job_templates(apps, schema_editor):
    _migrate_scan_job_templates(apps)
