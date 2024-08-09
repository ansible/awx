# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import json

# Django
from django.conf import settings  # noqa
from django.db import connection
from django.db.models.signals import pre_delete  # noqa

# django-ansible-base
from ansible_base.resource_registry.fields import AnsibleResourceField
from ansible_base.rbac import permission_registry
from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment
from ansible_base.lib.utils.models import prevent_search
from ansible_base.lib.utils.models import user_summary_fields

# AWX
from awx.main.models.base import BaseModel, PrimordialModel, accepts_json, VERBOSITY_CHOICES  # noqa
from awx.main.models.unified_jobs import UnifiedJob, UnifiedJobTemplate, StdoutMaxBytesExceeded  # noqa
from awx.main.models.organization import Organization, Team, UserSessionMembership  # noqa
from awx.main.models.credential import Credential, CredentialType, CredentialInputSource, ManagedCredentialType, build_safe_env  # noqa
from awx.main.models.projects import Project, ProjectUpdate  # noqa
from awx.main.models.receptor_address import ReceptorAddress  # noqa
from awx.main.models.inventory import (  # noqa
    CustomInventoryScript,
    Group,
    Host,
    HostMetric,
    HostMetricSummaryMonthly,
    Inventory,
    InventoryConstructedInventoryMembership,
    InventorySource,
    InventoryUpdate,
    SmartInventoryMembership,
)
from awx.main.models.jobs import (  # noqa
    Job,
    JobHostSummary,
    JobLaunchConfig,
    JobTemplate,
    SystemJob,
    SystemJobTemplate,
)
from awx.main.models.events import (  # noqa
    AdHocCommandEvent,
    InventoryUpdateEvent,
    JobEvent,
    ProjectUpdateEvent,
    SystemJobEvent,
    UnpartitionedAdHocCommandEvent,
    UnpartitionedInventoryUpdateEvent,
    UnpartitionedJobEvent,
    UnpartitionedProjectUpdateEvent,
    UnpartitionedSystemJobEvent,
)
from awx.main.models.ad_hoc_commands import AdHocCommand  # noqa
from awx.main.models.schedules import Schedule  # noqa
from awx.main.models.execution_environments import ExecutionEnvironment  # noqa
from awx.main.models.activity_stream import ActivityStream  # noqa
from awx.main.models.ha import (  # noqa
    Instance,
    InstanceLink,
    InstanceGroup,
    TowerScheduleState,
)
from awx.main.models.rbac import (  # noqa
    Role,
    batch_role_ancestor_rebuilding,
    role_summary_fields_generator,
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR,
)
from awx.main.models.mixins import (  # noqa
    CustomVirtualEnvMixin,
    ExecutionEnvironmentMixin,
    ResourceMixin,
    SurveyJobMixin,
    SurveyJobTemplateMixin,
    TaskManagerInventoryUpdateMixin,
    TaskManagerJobMixin,
    TaskManagerProjectUpdateMixin,
    TaskManagerUnifiedJobMixin,
)
from awx.main.models.notifications import Notification, NotificationTemplate, JobNotificationMixin  # noqa
from awx.main.models.label import Label  # noqa
from awx.main.models.workflow import (  # noqa
    WorkflowJob,
    WorkflowJobNode,
    WorkflowJobOptions,
    WorkflowJobTemplate,
    WorkflowJobTemplateNode,
    WorkflowApproval,
    WorkflowApprovalTemplate,
)


# Add custom methods to User model for permissions checks.
from django.contrib.auth.models import User  # noqa
from awx.main.access import get_user_queryset, check_user_access, check_user_access_with_errors  # noqa


User.add_to_class('get_queryset', get_user_queryset)
User.add_to_class('can_access', check_user_access)
User.add_to_class('can_access_with_errors', check_user_access_with_errors)
User.add_to_class('resource', AnsibleResourceField(primary_key_field="id"))
User.add_to_class('summary_fields', user_summary_fields)


def convert_jsonfields():
    if connection.vendor != 'postgresql':
        return

    # fmt: off
    fields = [
        ('main_activitystream', 'id', (
            'deleted_actor',
            'setting',
        )),
        ('main_job', 'unifiedjob_ptr_id', (
            'survey_passwords',
        )),
        ('main_joblaunchconfig', 'id', (
            'char_prompts',
            'survey_passwords',
        )),
        ('main_notification', 'id', (
            'body',
        )),
        ('main_unifiedjob', 'id', (
            'job_env',
        )),
        ('main_workflowjob', 'unifiedjob_ptr_id', (
            'char_prompts',
            'survey_passwords',
        )),
        ('main_workflowjobnode', 'id', (
            'char_prompts',
            'survey_passwords',
        )),
    ]
    # fmt: on

    with connection.cursor() as cursor:
        for table, pkfield, columns in fields:
            # Do the renamed old columns still exist?  If so, run the task.
            old_columns = ','.join(f"'{column}_old'" for column in columns)
            cursor.execute(
                f"""
                select count(1) from information_schema.columns
                where
                  table_name = %s and column_name in ({old_columns});
                """,
                (table,),
            )
            if cursor.fetchone()[0]:
                from awx.main.tasks.system import migrate_jsonfield

                migrate_jsonfield.apply_async([table, pkfield, columns])


def cleanup_created_modified_by(sender, **kwargs):
    # work around a bug in django-polymorphic that doesn't properly
    # handle cascades for reverse foreign keys on the polymorphic base model
    # https://github.com/django-polymorphic/django-polymorphic/issues/229
    for cls in (UnifiedJobTemplate, UnifiedJob):
        cls.objects.filter(created_by=kwargs['instance']).update(created_by=None)
        cls.objects.filter(modified_by=kwargs['instance']).update(modified_by=None)


pre_delete.connect(cleanup_created_modified_by, sender=User)


@property
def user_get_organizations(user):
    return Organization.access_qs(user, 'member')


@property
def user_get_admin_of_organizations(user):
    return Organization.access_qs(user, 'change')


@property
def user_get_auditor_of_organizations(user):
    return Organization.access_qs(user, 'audit')


@property
def created(user):
    return user.date_joined


User.add_to_class('organizations', user_get_organizations)
User.add_to_class('admin_of_organizations', user_get_admin_of_organizations)
User.add_to_class('auditor_of_organizations', user_get_auditor_of_organizations)
User.add_to_class('created', created)


def get_system_auditor_role():
    rd, created = RoleDefinition.objects.get_or_create(
        name='Controller System Auditor', defaults={'description': 'Migrated singleton role giving read permission to everything'}
    )
    if created:
        rd.permissions.add(*list(permission_registry.permission_qs.filter(codename__startswith='view')))
    return rd


@property
def user_is_system_auditor(user):
    if not hasattr(user, '_is_system_auditor'):
        if user.pk:
            rd = get_system_auditor_role()
            user._is_system_auditor = RoleUserAssignment.objects.filter(user=user, role_definition=rd).exists()
        else:
            # Odd case where user is unsaved, this should never be relied on
            return False
    return user._is_system_auditor


@user_is_system_auditor.setter
def user_is_system_auditor(user, tf):
    if not user.id:
        # If the user doesn't have a primary key yet (i.e., this is the *first*
        # time they've logged in, and we've just created the new User in this
        # request), we need one to set up the system auditor role
        user.save()
    rd = get_system_auditor_role()
    assignment = RoleUserAssignment.objects.filter(user=user, role_definition=rd).first()
    prior_value = bool(assignment)
    if prior_value != bool(tf):
        if assignment:
            assignment.delete()
        else:
            rd.give_global_permission(user)
        user._is_system_auditor = bool(tf)
        entry = ActivityStream.objects.create(changes=json.dumps({"is_system_auditor": [prior_value, bool(tf)]}), object1='user', operation='update')
        entry.user.add(user)


User.add_to_class('is_system_auditor', user_is_system_auditor)


from awx.main.registrar import activity_stream_registrar  # noqa

activity_stream_registrar.connect(Organization)
activity_stream_registrar.connect(Inventory)
activity_stream_registrar.connect(Host)
activity_stream_registrar.connect(Group)
activity_stream_registrar.connect(Instance)
activity_stream_registrar.connect(InstanceGroup)
activity_stream_registrar.connect(InventorySource)
# activity_stream_registrar.connect(InventoryUpdate)
activity_stream_registrar.connect(Credential)
activity_stream_registrar.connect(CredentialType)
activity_stream_registrar.connect(Team)
activity_stream_registrar.connect(Project)
# activity_stream_registrar.connect(ProjectUpdate)
activity_stream_registrar.connect(ExecutionEnvironment)
activity_stream_registrar.connect(JobTemplate)
activity_stream_registrar.connect(Job)
activity_stream_registrar.connect(AdHocCommand)
# activity_stream_registrar.connect(JobHostSummary)
# activity_stream_registrar.connect(JobEvent)
activity_stream_registrar.connect(Schedule)
activity_stream_registrar.connect(NotificationTemplate)
activity_stream_registrar.connect(Notification)
activity_stream_registrar.connect(Label)
activity_stream_registrar.connect(User)
activity_stream_registrar.connect(WorkflowJobTemplate)
activity_stream_registrar.connect(WorkflowJobTemplateNode)
activity_stream_registrar.connect(WorkflowJob)
activity_stream_registrar.connect(WorkflowApproval)
activity_stream_registrar.connect(WorkflowApprovalTemplate)

# Register models
permission_registry.register(Project, Team, WorkflowJobTemplate, JobTemplate, Inventory, Organization, Credential, NotificationTemplate, ExecutionEnvironment)
permission_registry.register(InstanceGroup, parent_field_name=None)  # Not part of an organization

# prevent API filtering on certain Django-supplied sensitive fields
prevent_search(User._meta.get_field('password'))
