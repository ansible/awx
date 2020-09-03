# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.conf import settings # noqa
from django.db import connection
from django.db.models.signals import pre_delete  # noqa

# AWX
from awx.main.models.base import (  # noqa
    BaseModel, PrimordialModel, prevent_search, accepts_json,
    CLOUD_INVENTORY_SOURCES, VERBOSITY_CHOICES
)
from awx.main.models.unified_jobs import (  # noqa
    UnifiedJob, UnifiedJobTemplate, StdoutMaxBytesExceeded
)
from awx.main.models.organization import (  # noqa
    Organization, Profile, Team, UserSessionMembership
)
from awx.main.models.credential import (  # noqa
    Credential, CredentialType, CredentialInputSource, ManagedCredentialType, build_safe_env
)
from awx.main.models.projects import Project, ProjectUpdate  # noqa
from awx.main.models.inventory import (  # noqa
    CustomInventoryScript, Group, Host, Inventory, InventorySource,
    InventoryUpdate, SmartInventoryMembership
)
from awx.main.models.jobs import (  # noqa
    Job, JobHostSummary, JobLaunchConfig, JobTemplate, SystemJob,
    SystemJobTemplate,
)
from awx.main.models.events import (  # noqa
    AdHocCommandEvent, InventoryUpdateEvent, JobEvent, ProjectUpdateEvent,
    SystemJobEvent,
)
from awx.main.models.ad_hoc_commands import AdHocCommand # noqa
from awx.main.models.schedules import Schedule # noqa
from awx.main.models.activity_stream import ActivityStream # noqa
from awx.main.models.ha import (  # noqa
    Instance, InstanceGroup, TowerScheduleState,
)
from awx.main.models.rbac import (  # noqa
    Role, batch_role_ancestor_rebuilding, get_roles_on_resource,
    role_summary_fields_generator, ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR,
)
from awx.main.models.mixins import (  # noqa
    CustomVirtualEnvMixin, ResourceMixin, SurveyJobMixin,
    SurveyJobTemplateMixin, TaskManagerInventoryUpdateMixin,
    TaskManagerJobMixin, TaskManagerProjectUpdateMixin,
    TaskManagerUnifiedJobMixin,
)
from awx.main.models.notifications import (  # noqa
    Notification, NotificationTemplate,
    JobNotificationMixin
)
from awx.main.models.label import Label # noqa
from awx.main.models.workflow import (  # noqa
    WorkflowJob, WorkflowJobNode, WorkflowJobOptions, WorkflowJobTemplate,
    WorkflowJobTemplateNode, WorkflowApproval, WorkflowApprovalTemplate,
)
from awx.api.versioning import reverse
from awx.main.models.oauth import ( # noqa
    OAuth2AccessToken, OAuth2Application
)
from oauth2_provider.models import Grant, RefreshToken # noqa -- needed django-oauth-toolkit model migrations


# Add custom methods to User model for permissions checks.
from django.contrib.auth.models import User  # noqa
from awx.main.access import (  # noqa
    get_user_queryset, check_user_access, check_user_access_with_errors,
    user_accessible_objects
)


User.add_to_class('get_queryset', get_user_queryset)
User.add_to_class('can_access', check_user_access)
User.add_to_class('can_access_with_errors', check_user_access_with_errors)
User.add_to_class('accessible_objects', user_accessible_objects)


def enforce_bigint_pk_migration():
    # see: https://github.com/ansible/awx/issues/6010
    # look at all the event tables and verify that they have been fully migrated
    # from the *old* int primary key table to the replacement bigint table
    # if not, attempt to migrate them in the background
    for tblname in (
        'main_jobevent', 'main_inventoryupdateevent',
        'main_projectupdateevent', 'main_adhoccommandevent',
        'main_systemjobevent'
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT 1 FROM information_schema.tables WHERE table_name=%s',
                (f'_old_{tblname}',)
            )
            if bool(cursor.rowcount):
                from awx.main.tasks import migrate_legacy_event_data
                migrate_legacy_event_data.apply_async([tblname])


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
    return Organization.objects.filter(member_role__members=user)


@property
def user_get_admin_of_organizations(user):
    return Organization.objects.filter(admin_role__members=user)


@property
def user_get_auditor_of_organizations(user):
    return Organization.objects.filter(auditor_role__members=user)


@property
def created(user):
    return user.date_joined


User.add_to_class('organizations', user_get_organizations)
User.add_to_class('admin_of_organizations', user_get_admin_of_organizations)
User.add_to_class('auditor_of_organizations', user_get_auditor_of_organizations)
User.add_to_class('created', created)


@property
def user_is_system_auditor(user):
    if not hasattr(user, '_is_system_auditor'):
        if user.pk:
            user._is_system_auditor = user.roles.filter(
                singleton_name='system_auditor', role_field='system_auditor').exists()
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
    if tf:
        role = Role.singleton('system_auditor')
        # must check if member to not duplicate activity stream
        if user not in role.members.all():
            role.members.add(user)
        user._is_system_auditor = True
    else:
        role = Role.singleton('system_auditor')
        if user in role.members.all():
            role.members.remove(user)
        user._is_system_auditor = False


User.add_to_class('is_system_auditor', user_is_system_auditor)


def user_is_in_enterprise_category(user, category):
    ret = (category,) in user.enterprise_auth.values_list('provider') and not user.has_usable_password()
    # NOTE: this if-else block ensures existing enterprise users are still able to
    # log in. Remove it in a future release
    if category == 'radius':
        ret = ret or not user.has_usable_password()
    elif category == 'saml':
        ret = ret or user.social_auth.all()
    return ret


User.add_to_class('is_in_enterprise_category', user_is_in_enterprise_category)




def o_auth2_application_get_absolute_url(self, request=None):
    return reverse('api:o_auth2_application_detail', kwargs={'pk': self.pk}, request=request)


OAuth2Application.add_to_class('get_absolute_url', o_auth2_application_get_absolute_url)


def o_auth2_token_get_absolute_url(self, request=None):
    return reverse('api:o_auth2_token_detail', kwargs={'pk': self.pk}, request=request)


OAuth2AccessToken.add_to_class('get_absolute_url', o_auth2_token_get_absolute_url)

from awx.main.registrar import activity_stream_registrar # noqa
activity_stream_registrar.connect(Organization)
activity_stream_registrar.connect(Inventory)
activity_stream_registrar.connect(Host)
activity_stream_registrar.connect(Group)
activity_stream_registrar.connect(InventorySource)
#activity_stream_registrar.connect(InventoryUpdate)
activity_stream_registrar.connect(Credential)
activity_stream_registrar.connect(CredentialType)
activity_stream_registrar.connect(Team)
activity_stream_registrar.connect(Project)
#activity_stream_registrar.connect(ProjectUpdate)
activity_stream_registrar.connect(JobTemplate)
activity_stream_registrar.connect(Job)
activity_stream_registrar.connect(AdHocCommand)
# activity_stream_registrar.connect(JobHostSummary)
# activity_stream_registrar.connect(JobEvent)
# activity_stream_registrar.connect(Profile)
activity_stream_registrar.connect(Schedule)
activity_stream_registrar.connect(CustomInventoryScript)
activity_stream_registrar.connect(NotificationTemplate)
activity_stream_registrar.connect(Notification)
activity_stream_registrar.connect(Label)
activity_stream_registrar.connect(User)
activity_stream_registrar.connect(WorkflowJobTemplate)
activity_stream_registrar.connect(WorkflowJobTemplateNode)
activity_stream_registrar.connect(WorkflowJob)
activity_stream_registrar.connect(WorkflowApproval)
activity_stream_registrar.connect(WorkflowApprovalTemplate)
activity_stream_registrar.connect(OAuth2Application)
activity_stream_registrar.connect(OAuth2AccessToken)

# prevent API filtering on certain Django-supplied sensitive fields
prevent_search(User._meta.get_field('password'))
prevent_search(OAuth2AccessToken._meta.get_field('token'))
prevent_search(RefreshToken._meta.get_field('token'))
prevent_search(OAuth2Application._meta.get_field('client_secret'))
prevent_search(OAuth2Application._meta.get_field('client_id'))
prevent_search(Grant._meta.get_field('code'))
