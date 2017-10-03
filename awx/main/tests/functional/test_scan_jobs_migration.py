# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.
import pytest

from django.apps import apps

from awx.main.models.base import PERM_INVENTORY_SCAN, PERM_INVENTORY_DEPLOY
from awx.main.models import (
    JobTemplate,
    Project,
    Inventory,
    Organization,
)

from awx.main.migrations._scan_jobs import _migrate_scan_job_templates


@pytest.fixture
def organizations():
    return [Organization.objects.create(name=u"org-\xe9-{}".format(x)) for x in range(3)]


@pytest.fixture
def inventories(organizations):
    return [Inventory.objects.create(name=u"inv-\xe9-{}".format(x), 
                                     organization=organizations[x]) for x in range(3)]


@pytest.fixture
def job_templates_scan(inventories):
    return [JobTemplate.objects.create(name=u"jt-\xe9-scan-{}".format(x), 
                                       job_type=PERM_INVENTORY_SCAN,
                                       inventory=inventories[x]) for x in range(3)]


@pytest.fixture
def job_templates_deploy(inventories):
    return [JobTemplate.objects.create(name=u"jt-\xe9-deploy-{}".format(x), 
                                       job_type=PERM_INVENTORY_DEPLOY,
                                       inventory=inventories[x]) for x in range(3)]


@pytest.fixture
def project_custom(organizations):
    return Project.objects.create(name=u"proj-\xe9-scan_custom", 
                                  scm_url='https://giggity.com',
                                  organization=organizations[0])


@pytest.fixture
def job_templates_custom_scan_project(project_custom):
    return [JobTemplate.objects.create(name=u"jt-\xe9-scan-custom-{}".format(x), 
                                       project=project_custom, 
                                       job_type=PERM_INVENTORY_SCAN) for x in range(3)]


@pytest.fixture
def job_template_scan_no_org():
    return JobTemplate.objects.create(name=u"jt-\xe9-scan-no-org",
                                      job_type=PERM_INVENTORY_SCAN)


@pytest.mark.django_db
def test_scan_jobs_migration(job_templates_scan, job_templates_deploy, job_templates_custom_scan_project, project_custom, job_template_scan_no_org):
    _migrate_scan_job_templates(apps)

    # Ensure there are no scan job templates after the migration
    assert 0 == JobTemplate.objects.filter(job_type=PERM_INVENTORY_SCAN).count()

    # Ensure special No Organization proj created
    # And No Organization project is associated with correct jt
    proj = Project.objects.get(name="Tower Fact Scan - No Organization")
    assert proj.id == JobTemplate.objects.get(id=job_template_scan_no_org.id).project.id

    # Ensure per-org projects were created
    projs = Project.objects.filter(name__startswith="Tower Fact Scan")
    assert projs.count() == 4

    # Ensure scan job templates with Tower project are migrated
    for i, jt_old in enumerate(job_templates_scan):
        jt = JobTemplate.objects.get(id=jt_old.id)
        assert PERM_INVENTORY_DEPLOY == jt.job_type
        assert jt.use_fact_cache is True
        assert projs[i] == jt.project

    # Ensure scan job templates with custom projects are migrated
    for jt_old in job_templates_custom_scan_project:
        jt = JobTemplate.objects.get(id=jt_old.id)
        assert PERM_INVENTORY_DEPLOY == jt.job_type
        assert jt.use_fact_cache is True
        assert project_custom == jt.project

    # Ensure other job template aren't touched
    for jt_old in job_templates_deploy:
        jt = JobTemplate.objects.get(id=jt_old.id)
        assert PERM_INVENTORY_DEPLOY == jt.job_type
        assert jt.project is None

