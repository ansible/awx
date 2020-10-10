# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.



# Django
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils.timezone import now as tz_now
from django.utils.translation import ugettext_lazy as _


# AWX
from awx.api.versioning import reverse
from awx.main.fields import (
    AutoOneToOneField, ImplicitRoleField, OrderedManyToManyField
)
from awx.main.models.base import (
    BaseModel, CommonModel, CommonModelNameNotUnique, CreatedModifiedModel,
    NotificationFieldsModel
)
from awx.main.models.rbac import (
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR,
)
from awx.main.models.unified_jobs import UnifiedJob
from awx.main.models.mixins import ResourceMixin, CustomVirtualEnvMixin, RelatedJobsMixin

__all__ = ['Organization', 'Team', 'Profile', 'UserSessionMembership']


class Organization(CommonModel, NotificationFieldsModel, ResourceMixin, CustomVirtualEnvMixin, RelatedJobsMixin):
    '''
    An organization is the basic unit of multi-tenancy divisions
    '''

    class Meta:
        app_label = 'main'
        ordering = ('name',)

    instance_groups = OrderedManyToManyField(
        'InstanceGroup',
        blank=True,
        through='OrganizationInstanceGroupMembership'
    )
    galaxy_credentials = OrderedManyToManyField(
        'Credential',
        blank=True,
        through='OrganizationGalaxyCredentialMembership',
        related_name='%(class)s_galaxy_credentials'
    )
    max_hosts = models.PositiveIntegerField(
        blank=True,
        default=0,
        help_text=_('Maximum number of hosts allowed to be managed by this organization.'),
    )
    notification_templates_approvals = models.ManyToManyField(
        "NotificationTemplate",
        blank=True,
        related_name='%(class)s_notification_templates_for_approvals'
    )

    admin_role = ImplicitRoleField(
        parent_role='singleton:' + ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    )
    execute_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    project_admin_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    inventory_admin_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    credential_admin_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    workflow_admin_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    notification_admin_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    job_template_admin_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    auditor_role = ImplicitRoleField(
        parent_role='singleton:' + ROLE_SINGLETON_SYSTEM_AUDITOR,
    )
    member_role = ImplicitRoleField(
        parent_role=['admin_role']
    )
    read_role = ImplicitRoleField(
        parent_role=['member_role', 'auditor_role',
                     'execute_role', 'project_admin_role',
                     'inventory_admin_role', 'workflow_admin_role',
                     'notification_admin_role', 'credential_admin_role',
                     'job_template_admin_role', 'approval_role',],
    )
    approval_role = ImplicitRoleField(
        parent_role='admin_role',
    )


    def get_absolute_url(self, request=None):
        return reverse('api:organization_detail', kwargs={'pk': self.pk}, request=request)

    '''
    RelatedJobsMixin
    '''
    def _get_related_jobs(self):
        return UnifiedJob.objects.non_polymorphic().filter(organization=self)


class OrganizationGalaxyCredentialMembership(models.Model):

    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE
    )
    credential = models.ForeignKey(
        'Credential',
        on_delete=models.CASCADE
    )
    position = models.PositiveIntegerField(
        null=True,
        default=None,
        db_index=True,
    )


class Team(CommonModelNameNotUnique, ResourceMixin):
    '''
    A team is a group of users that work on common projects.
    '''

    class Meta:
        app_label = 'main'
        unique_together = [('organization', 'name')]
        ordering = ('organization__name', 'name')

    organization = models.ForeignKey(
        'Organization',
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='teams',
    )
    admin_role = ImplicitRoleField(
        parent_role='organization.admin_role',
    )
    member_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    read_role = ImplicitRoleField(
        parent_role=['organization.auditor_role', 'member_role'],
    )

    def get_absolute_url(self, request=None):
        return reverse('api:team_detail', kwargs={'pk': self.pk}, request=request)


class Profile(CreatedModifiedModel):
    '''
    Profile model related to User object. Currently stores LDAP DN for users
    loaded from LDAP.
    '''

    class Meta:
        app_label = 'main'

    user = AutoOneToOneField(
        'auth.User',
        related_name='profile',
        editable=False,
        on_delete=models.CASCADE
    )
    ldap_dn = models.CharField(
        max_length=1024,
        default='',
    )


class UserSessionMembership(BaseModel):
    '''
    A lookup table for API session membership given user. Note, there is a
    different session created by channels for websockets using the same
    underlying model.
    '''

    class Meta:
        app_label = 'main'

    user = models.ForeignKey(
        'auth.User', related_name='+', blank=False, null=False, on_delete=models.CASCADE
    )
    session = models.OneToOneField(
        Session, related_name='+', blank=False, null=False, on_delete=models.CASCADE
    )
    created = models.DateTimeField(default=None, editable=False)

    @staticmethod
    def get_memberships_over_limit(user_id, now=None):
        if settings.SESSIONS_PER_USER == -1:
            return []
        if now is None:
            now = tz_now()
        query_set = UserSessionMembership.objects\
            .select_related('session')\
            .filter(user_id=user_id)\
            .order_by('-created')
        non_expire_memberships = [x for x in query_set if x.session.expire_date > now]
        return non_expire_memberships[settings.SESSIONS_PER_USER:]


# Add get_absolute_url method to User model if not present.
if not hasattr(User, 'get_absolute_url'):
    def user_get_absolute_url(user, request=None):
        return reverse('api:user_detail', kwargs={'pk': user.pk}, request=request)
    User.add_to_class('get_absolute_url', user_get_absolute_url)
