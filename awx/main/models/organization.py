# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import hashlib
import hmac
import uuid

# Django
from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now

# AWX
from awx.main.fields import AutoOneToOneField
from awx.main.models.base import * # noqa

__all__ = ['Organization', 'Team', 'Permission', 'Profile', 'AuthToken']


class Organization(CommonModel):
    '''
    An organization is the basic unit of multi-tenancy divisions
    '''

    class Meta:
        app_label = 'main'
        ordering = ('name',)

    users = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='organizations',
    )
    admins = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='admin_of_organizations',
    )
    projects = models.ManyToManyField(
        'Project',
        blank=True,
        related_name='organizations',
    )

    def get_absolute_url(self):
        return reverse('api:organization_detail', args=(self.pk,))

    def __unicode__(self):
        return self.name


class Team(CommonModelNameNotUnique):
    '''
    A team is a group of users that work on common projects.
    '''

    class Meta:
        app_label = 'main'
        unique_together = [('organization', 'name')]
        ordering = ('organization__name', 'name')

    users = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='teams',
    )
    organization = models.ForeignKey(
        'Organization',
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
        related_name='teams',
    )
    projects = models.ManyToManyField(
        'Project',
        blank=True,
        related_name='teams',
    )

    def get_absolute_url(self):
        return reverse('api:team_detail', args=(self.pk,))

    def mark_inactive(self, save=True):
        '''
        When marking a team inactive we'll wipe out its credentials also
        '''
        for cred in self.credentials.all():
            cred.mark_inactive()
        super(Team, self).mark_inactive(save=save)

class Permission(CommonModelNameNotUnique):
    '''
    A permission allows a user, project, or team to be able to use an inventory source.
    '''

    class Meta:
        app_label = 'main'

    # permissions are granted to either a user or a team:
    user            = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL, blank=True, related_name='permissions')
    team            = models.ForeignKey('Team', null=True, on_delete=models.SET_NULL, blank=True, related_name='permissions')

    # to be used against a project or inventory (or a project and inventory in conjunction):
    project = models.ForeignKey(
        'Project',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='permissions',
    )
    inventory       = models.ForeignKey('Inventory', null=True, on_delete=models.SET_NULL, related_name='permissions')

    # permission system explanation:
    #
    # for example, user A on inventory X has write permissions                 (PERM_INVENTORY_WRITE)
    #              team C on inventory X has read permissions                  (PERM_INVENTORY_READ)
    #              user A can create job templates                             (PERM_JOBTEMPLATE_CREATE)
    #              team C on inventory X and project Y has launch permissions  (PERM_INVENTORY_DEPLOY)
    #              team C on inventory X and project Z has dry run permissions (PERM_INVENTORY_CHECK)
    #
    # basically for launching, permissions can be awarded to the whole inventory source or just the inventory source
    # in context of a given project.
    #
    # the project parameter is not used when dealing with READ, WRITE, or ADMIN permissions.

    permission_type = models.CharField(max_length=64, choices=PERMISSION_TYPE_CHOICES)
    run_ad_hoc_commands = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode("Permission(name=%s,ON(user=%s,team=%s),FOR(project=%s,inventory=%s,type=%s%s))" % (
            self.name,
            self.user,
            self.team,
            self.project,
            self.inventory,
            self.permission_type,
            '+adhoc' if self.run_ad_hoc_commands else '',
        ))

    def get_absolute_url(self):
        return reverse('api:permission_detail', args=(self.pk,))


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
    )
    ldap_dn = models.CharField(
        max_length=1024,
        default='',
    )


class AuthToken(BaseModel):
    '''
    Custom authentication tokens per user with expiration and request-specific
    data.
    '''

    class Meta:
        app_label = 'main'
    
    key = models.CharField(max_length=40, primary_key=True)
    user = models.ForeignKey('auth.User', related_name='auth_tokens',
                             on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    expires = models.DateTimeField(default=now)
    request_hash = models.CharField(max_length=40, blank=True, default='')

    @classmethod
    def get_request_hash(cls, request):
        h = hashlib.sha1()
        h.update(settings.SECRET_KEY)
        for header in settings.REMOTE_HOST_HEADERS:
            value = request.META.get(header, '').split(',')[0].strip()
            if value:
                h.update(value)
                break
        h.update(request.META.get('HTTP_USER_AGENT', ''))
        return h.hexdigest()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.refresh(save=False)
        if not self.key:
            self.key = self.generate_key()
        return super(AuthToken, self).save(*args, **kwargs)

    def refresh(self, save=True):
        if not self.pk or not self.expired:
            self.expires = now() + datetime.timedelta(seconds=settings.AUTH_TOKEN_EXPIRATION)
            if save:
                self.save()

    def invalidate(self, save=True):
        if not self.expired:
            self.expires = now() - datetime.timedelta(seconds=1)
            if save:
                self.save()

    def generate_key(self):
        unique = uuid.uuid4()
        return hmac.new(unique.bytes, digestmod=hashlib.sha1).hexdigest()

    @property
    def expired(self):
        return bool(self.expires < now())

    def __unicode__(self):
        return self.key


# Add mark_inactive method to User model.
def user_mark_inactive(user, save=True):
    '''Use instead of delete to rename and mark users inactive.'''
    if user.is_active:
        # Set timestamp to datetime.isoformat() but without the time zone
        # offset to stay withint the 30 character username limit.
        dtnow = now()
        deleted_ts = dtnow.strftime('%Y-%m-%dT%H:%M:%S.%f')
        user.username = '_d_%s' % deleted_ts
        user.is_active = False
        if save:
            user.save()
            
User.add_to_class('mark_inactive', user_mark_inactive)
