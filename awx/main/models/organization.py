# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
import hashlib
import hmac
import uuid

# Django
from django.conf import settings
from django.db import models, connection
from django.contrib.auth.models import User
from django.utils.timezone import now as tz_now
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.api.versioning import reverse
from awx.main.fields import AutoOneToOneField, ImplicitRoleField
from awx.main.models.base import * # noqa
from awx.main.models.rbac import (
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR,
)
from awx.main.models.mixins import ResourceMixin

__all__ = ['Organization', 'Team', 'Profile', 'AuthToken']


class Organization(CommonModel, NotificationFieldsModel, ResourceMixin):
    '''
    An organization is the basic unit of multi-tenancy divisions
    '''

    class Meta:
        app_label = 'main'
        ordering = ('name',)

    instance_groups = models.ManyToManyField(
        'InstanceGroup',
        blank=True,
    )
    admin_role = ImplicitRoleField(
        parent_role='singleton:' + ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    )
    auditor_role = ImplicitRoleField(
        parent_role='singleton:' + ROLE_SINGLETON_SYSTEM_AUDITOR,
    )
    member_role = ImplicitRoleField(
        parent_role='admin_role',
    )
    read_role = ImplicitRoleField(
        parent_role=['member_role', 'auditor_role'],
    )


    def get_absolute_url(self, request=None):
        return reverse('api:organization_detail', kwargs={'pk': self.pk}, request=request)

    def __unicode__(self):
        return self.name


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
    )
    ldap_dn = models.CharField(
        max_length=1024,
        default='',
    )


"""
Since expiration and session expiration is event driven a token could be
invalidated for both reasons. Further, we only support a single reason for a
session token being invalid. For this case, mark the token as expired.

Note: Again, because the value of reason is event based. The reason may not be
set (i.e. may equal '') even though a session is expired or a limit is reached.
"""


class AuthToken(BaseModel):
    '''
    Custom authentication tokens per user with expiration and request-specific
    data.
    '''

    REASON_CHOICES = [
        ('', _('Token not invalidated')),
        ('timeout_reached', _('Token is expired')),
        ('limit_reached', _('The maximum number of allowed sessions for this user has been exceeded.')),
        # invalid_token is not a used data-base value, but is returned by the
        # api when a token is not found
        ('invalid_token', _('Invalid token')),
    ]

    class Meta:
        app_label = 'main'

    key = models.CharField(max_length=40, primary_key=True)
    user = prevent_search(models.ForeignKey('auth.User',
                          related_name='auth_tokens', on_delete=models.CASCADE))
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    expires = models.DateTimeField(default=tz_now)
    request_hash = prevent_search(models.CharField(max_length=40, blank=True,
                                                   default=''))
    reason = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Reason the auth token was invalidated.')
    )

    @staticmethod
    def reason_long(reason):
        for x in AuthToken.REASON_CHOICES:
            if x[0] == reason:
                return unicode(x[1])
        return None

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

    def refresh(self, now=None, save=True):
        if not now:
            now = tz_now()
        if not self.pk or not self.is_expired(now=now):
            self.expires = now + datetime.timedelta(seconds=settings.AUTH_TOKEN_EXPIRATION)
            if save:
                connection.on_commit(lambda: self.save(update_fields=['expires']))

    def invalidate(self, reason='timeout_reached', save=True):
        if not AuthToken.reason_long(reason):
            raise ValueError(_('Invalid reason specified'))
        self.reason = reason
        if save:
            self.save()
        return reason

    @staticmethod
    def get_tokens_over_limit(user, now=None):
        if now is None:
            now = tz_now()
        invalid_tokens = AuthToken.objects.none()
        if settings.AUTH_TOKEN_PER_USER != -1:
            invalid_tokens = AuthToken.objects.filter(
                user=user,
                expires__gt=now,
                reason='',
            ).order_by('-created')[settings.AUTH_TOKEN_PER_USER:]
        return invalid_tokens

    def generate_key(self):
        unique = uuid.uuid4()
        return hmac.new(unique.bytes, digestmod=hashlib.sha1).hexdigest()

    def is_expired(self, now=None):
        if not now:
            now = tz_now()
        return bool(self.expires < now)

    @property
    def invalidated(self):
        return bool(self.reason != '')

    """
    Token is valid if it's in the set of unexpired tokens.
    The unexpired token set is:
        * tokens not expired
        * limited to number of tokens per-user
        * sorted by created on date
    """
    def in_valid_tokens(self, now=None):
        if not now:
            now = tz_now()
        valid_n_tokens_qs = self.user.auth_tokens.filter(
            expires__gt=now,
            reason='',
        ).order_by('-created')
        if settings.AUTH_TOKEN_PER_USER != -1:
            valid_n_tokens_qs = valid_n_tokens_qs[0:settings.AUTH_TOKEN_PER_USER]
        valid_n_tokens = valid_n_tokens_qs.values_list('key', flat=True)

        return bool(self.key in valid_n_tokens)

    def __unicode__(self):
        return self.key


# Add get_absolute_url method to User model if not present.
if not hasattr(User, 'get_absolute_url'):
    def user_get_absolute_url(user, request=None):
        return reverse('api:user_detail', kwargs={'pk': user.pk}, request=request)
    User.add_to_class('get_absolute_url', user_get_absolute_url)
