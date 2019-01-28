import os.path

from django.db.models import Count
from django.conf import settings

from awx.conf.license import get_license
from awx.main.utils import (get_awx_version, get_ansible_version,
                            get_custom_venv_choices, camelcase_to_underscore)
from awx.main import models
from awx.main.analytics import register


#
# This module is used to define metrics collected by awx.main.analytics.gather()
# Each function is decorated with a key name, and should return a data
# structure that can be serialized to JSON
#
# @register('something')
# def something(since):
#     # the generated archive will contain a `something.json` w/ this JSON
#     return {'some': 'json'}
#
# All functions - when called - will be passed a datetime.datetime object,
# `since`, which represents the last time analytics were gathered (some metrics
# functions - like those that return metadata about playbook runs, may return
# data _since_ the last report date - i.e., new data in the last 24 hours)
#


@register('config')
def config(since):
    license_data = get_license(show_key=False)
    return {
        'system_uuid': settings.SYSTEM_UUID,
        'version': get_awx_version(),
        'ansible_version': get_ansible_version(),
        'license_type': license_data.get('license_type', 'UNLICENSED')
    }


@register('counts')
def counts(since):
    counts = {}
    for cls in (models.Organization, models.Team, models.User,
                models.Inventory, models.Credential, models.Project,
                models.JobTemplate, models.WorkflowJobTemplate, models.Host,
                models.Schedule, models.CustomInventoryScript):
        counts[camelcase_to_underscore(cls.__name__)] = cls.objects.count()

    venvs = get_custom_venv_choices()
    counts['custom_virtualenvs'] = len([
        v for v in venvs
        if os.path.basename(v.rstrip('/')) != 'ansible'
    ])
    return counts


@register('projects_by_scm_type')
def projects_by_scm_type(since):
    counts = dict(
        (t[0] or 'manual', 0)
        for t in models.Project.SCM_TYPE_CHOICES
    )
    for result in models.Project.objects.values('scm_type').annotate(
        count=Count('scm_type')
    ).order_by('scm_type'):
        counts[result['scm_type'] or 'manual'] = result['count']
    return counts
