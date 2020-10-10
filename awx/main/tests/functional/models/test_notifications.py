# -*- coding: utf-8 -*-
from copy import deepcopy
import datetime

import pytest

#from awx.main.models import NotificationTemplates, Notifications, JobNotificationMixin
from awx.main.models import (AdHocCommand, InventoryUpdate, Job, JobNotificationMixin, ProjectUpdate,
                             SystemJob, WorkflowJob)
from awx.api.serializers import UnifiedJobSerializer


class TestJobNotificationMixin(object):
    CONTEXT_STRUCTURE = {'job': {'allow_simultaneous': bool,
                                 'artifacts': {},
                                 'custom_virtualenv': str,
                                 'controller_node': str,
                                 'created': datetime.datetime,
                                 'description': str,
                                 'diff_mode': bool,
                                 'elapsed': float,
                                 'execution_node': str,
                                 'failed': bool,
                                 'finished': bool,
                                 'force_handlers': bool,
                                 'forks': int,
                                 'host_status_counts': {
                                     'skipped': int, 'ok': int, 'changed': int,
                                     'failures': int, 'dark': int, 'processed': int,
                                     'rescued': int, 'failed': bool
                                 },
                                 'id': int,
                                 'job_explanation': str,
                                 'job_slice_count': int,
                                 'job_slice_number': int,
                                 'job_tags': str,
                                 'job_type': str,
                                 'launch_type': str,
                                 'limit': str,
                                 'modified': datetime.datetime,
                                 'name': str,
                                 'playbook': str,
                                 'scm_branch': str,
                                 'scm_revision': str,
                                 'skip_tags': str,
                                 'start_at_task': str,
                                 'started': str,
                                 'status': str,
                                 'summary_fields': {'created_by': {'first_name': str,
                                                                   'id': int,
                                                                   'last_name': str,
                                                                   'username': str},
                                                    'instance_group': {'id': int, 'name': str},
                                                    'inventory': {'description': str,
                                                                  'has_active_failures': bool,
                                                                  'has_inventory_sources': bool,
                                                                  'hosts_with_active_failures': int,
                                                                  'id': int,
                                                                  'inventory_sources_with_failures': int,
                                                                  'kind': str,
                                                                  'name': str,
                                                                  'organization_id': int,
                                                                  'total_groups': int,
                                                                  'total_hosts': int,
                                                                  'total_inventory_sources': int},
                                                    'job_template': {'description': str,
                                                                     'id': int,
                                                                     'name': str},
                                                    'labels': {'count': int, 'results': list},
                                                    'project': {'description': str,
                                                                'id': int,
                                                                'name': str,
                                                                'scm_type': str,
                                                                'status': str},
                                                    'unified_job_template': {'description': str,
                                                                             'id': int,
                                                                             'name': str,
                                                                             'unified_job_type': str}},

                                 'timeout': int,
                                 'type': str,
                                 'url': str,
                                 'use_fact_cache': bool,
                                 'verbosity': int},
                         'job_friendly_name': str,
                         'job_metadata': str,
                         'approval_status': str,
                         'approval_node_name': str,
                         'workflow_url': str,
                         'url': str}


    @pytest.mark.django_db
    @pytest.mark.parametrize('JobClass', [AdHocCommand, InventoryUpdate, Job, ProjectUpdate, SystemJob, WorkflowJob])
    def test_context(self, JobClass, sqlite_copy_expert, project, inventory_source):
        """The Jinja context defines all of the fields that can be used by a template. Ensure that the context generated
        for each job type has the expected structure."""
        def check_structure(expected_structure, obj):
            if isinstance(expected_structure, dict):
                assert isinstance(obj, dict)
                for key in obj:
                    assert key in expected_structure
                    if obj[key] is None:
                        continue
                    if isinstance(expected_structure[key], dict):
                        assert isinstance(obj[key], dict)
                        check_structure(expected_structure[key], obj[key])
                    else:
                        if key == 'job_explanation':
                            assert isinstance(str(obj[key]), expected_structure[key])
                        else:
                            assert isinstance(obj[key], expected_structure[key])
        kwargs = {}
        if JobClass is InventoryUpdate:
            kwargs['inventory_source'] = inventory_source
            kwargs['source'] = inventory_source.source
        elif JobClass is ProjectUpdate:
            kwargs['project'] = project

        job = JobClass.objects.create(name='foo', **kwargs)
        job_serialization = UnifiedJobSerializer(job).to_representation(job)

        context = job.context(job_serialization)
        check_structure(TestJobNotificationMixin.CONTEXT_STRUCTURE, context)


    @pytest.mark.django_db
    def test_context_job_metadata_with_unicode(self):
        job = Job.objects.create(name='批量安装项目')
        job_serialization = UnifiedJobSerializer(job).to_representation(job)
        context = job.context(job_serialization)
        assert '批量安装项目' in context['job_metadata']


    def test_context_stub(self):
        """The context stub is a fake context used to validate custom notification messages. Ensure that
        this also has the expected structure. Furthermore, ensure that the stub context contains
        *all* fields that could possibly be included in a context."""
        def check_structure_and_completeness(expected_structure, obj):
            expected_structure = deepcopy(expected_structure)
            if isinstance(expected_structure, dict):
                assert isinstance(obj, dict)
                for key in obj:
                    assert key in expected_structure
                    # Context stub should not have any undefined fields
                    assert obj[key] is not None
                    if isinstance(expected_structure[key], dict):
                        assert isinstance(obj[key], dict)
                        check_structure_and_completeness(expected_structure[key], obj[key])
                        expected_structure.pop(key)
                    else:
                        assert isinstance(obj[key], expected_structure[key])
                        expected_structure.pop(key)
                # Ensure all items in expected structure were present
                assert not len(expected_structure)

        context_stub = JobNotificationMixin.context_stub()
        check_structure_and_completeness(TestJobNotificationMixin.CONTEXT_STRUCTURE, context_stub)
