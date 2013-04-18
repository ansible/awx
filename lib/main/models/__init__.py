# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.

from django.db import models, DatabaseError
from django.db.models import CASCADE, SET_NULL, PROTECT
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now
import exceptions
from jsonfield import JSONField
from djcelery.models import TaskMeta
from rest_framework.authtoken.models import Token

# TODO: jobs and events model TBD
# TODO: reporting model TBD

PERM_INVENTORY_ADMIN  = 'admin'
PERM_INVENTORY_READ   = 'read'
PERM_INVENTORY_WRITE  = 'write'
PERM_INVENTORY_DEPLOY = 'run'
PERM_INVENTORY_CHECK  = 'check'

JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, _('Run')),
    (PERM_INVENTORY_CHECK, _('Check')),
]

PERMISSION_TYPES = [
    PERM_INVENTORY_ADMIN,
    PERM_INVENTORY_READ,
    PERM_INVENTORY_WRITE,
    PERM_INVENTORY_DEPLOY,
    PERM_INVENTORY_CHECK,
]

PERMISSION_TYPES_ALLOWING_INVENTORY_READ = [
    PERM_INVENTORY_ADMIN,
    PERM_INVENTORY_WRITE,
    PERM_INVENTORY_READ,
]

PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE = [
    PERM_INVENTORY_ADMIN,
    PERM_INVENTORY_WRITE,
]

PERMISSION_TYPES_ALLOWING_INVENTORY_ADMIN = [
    PERM_INVENTORY_ADMIN,
]

# FIXME: TODO: make sure all of these are used and consistent
PERMISSION_TYPE_CHOICES = [
    (PERM_INVENTORY_READ, _('Read Inventory')),
    (PERM_INVENTORY_WRITE, _('Edit Inventory')),
    (PERM_INVENTORY_ADMIN, _('Administrate Inventory')),
    (PERM_INVENTORY_DEPLOY, _('Deploy To Inventory')),
    (PERM_INVENTORY_CHECK, _('Deploy To Inventory (Dry Run)')),
]

class EditHelper(object):

    @classmethod
    def illegal_changes(cls, request, obj, model_class):
        ''' have any illegal changes been made (for a PUT request)? '''
        can_admin = model_class.can_user_administrate(request.user, obj)
        if (not can_admin) or (can_admin == 'partial'):
            check_fields = model_class.admin_only_edit_fields
            changed = cls.fields_changed(check_fields, obj, request.DATA)
            if len(changed.keys()) > 0:
                return True
        return False

    @classmethod
    def fields_changed(cls, fields, obj, data):
        ''' return the fields that would be changed by a prospective PUT operation '''
        changed = {}
        for f in fields:
            left = getattr(obj, f, None)
            if left is None:
                raise Exception("internal error, %s is not a member of %s" % (f, obj))
            right = data.get(f, None)
            if (right is not None) and (left != right):
                changed[f] = (left, right)
        return changed

class UserHelper(object):

    # fields that the user themselves cannot edit, but are not actually read only
    admin_only_edit_fields = ('last_name', 'first_name', 'username', 'is_active', 'is_superuser')

    @classmethod
    def can_user_administrate(cls, user, obj):
        ''' a user can be administrated if they are themselves, or by org admins or superusers '''
        if user == obj:
            return 'partial'
        if user.is_superuser:
            return True
        matching_orgs = obj.organizations.filter(admins__in = [user]).count()
        return matching_orgs

    @classmethod
    def can_user_read(cls, user, obj):
        ''' a user can be read if they are on the same team or can be administrated '''
        matching_teams = user.teams.filter(users__in = [ user ]).count()
        return matching_teams or cls.can_user_administrate(user, obj)

    @classmethod
    def can_user_delete(cls, user, obj):
        if user.is_superuser:
            return True
        matching_orgs = obj.organizations.filter(admins__in = [user]).count()
        return matching_orgs

    @classmethod
    def can_user_attach(cls, user, obj, sub_obj, relationship_type):
        if type(sub_obj) != User:
            if not sub_obj.can_user_read(user, sub_obj):
                return False
        rc = cls.can_user_administrate(user, obj)
        return rc

    @classmethod
    def can_user_unattach(cls, user, obj, sub_obj, relationship_type):
        return cls.can_user_administrate(user, obj)

class PrimordialModel(models.Model):
    '''
    common model for all object types that have these standard fields
    must use a subclass CommonModel or CommonModelNameNotUnique though
    as this lacks a name field.
    '''

    class Meta:
        abstract = True

    description   = models.TextField(blank=True, default='')
    created_by    = models.ForeignKey('auth.User', on_delete=SET_NULL, null=True, related_name='%s(class)s_created', editable=False) # not blank=False on purpose for admin!
    creation_date = models.DateField(auto_now_add=True)
    tags          = models.ManyToManyField('Tag', related_name='%(class)s_by_tag', blank=True)
    audit_trail   = models.ManyToManyField('AuditTrail', related_name='%(class)s_by_audit_trail', blank=True)
    active        = models.BooleanField(default=True)

    def __unicode__(self):
        return unicode("%s-%s"% (self.name, self.id))

    @classmethod
    def can_user_administrate(cls, user, obj):
        # FIXME: do we want a seperate method to override put?  This is kind of general purpose
        raise exceptions.NotImplementedError()

    @classmethod
    def can_user_delete(cls, user, obj):
        raise exceptions.NotImplementedError()

    @classmethod
    def can_user_read(cls, user, obj):
        raise exceptions.NotImplementedError()

    @classmethod
    def can_user_add(cls, user, data):
        return user.is_superuser

    @classmethod
    def can_user_attach(cls, user, obj, sub_obj, relationship_type):
        ''' whether you can add sub_obj to obj using the relationship type in a subobject view '''
        if type(sub_obj) != User:
            if not sub_obj.can_user_read(user, sub_obj):
                return False
        rc = cls.can_user_administrate(user, obj)
        return rc

    @classmethod
    def can_user_unattach(cls, user, obj, sub_obj, relationship):
        return cls.can_user_administrate(user, obj)

class CommonModel(PrimordialModel):
    ''' a base model where the name is unique '''

    class Meta:
        abstract = True

    name          = models.CharField(max_length=512, unique=True)

class CommonModelNameNotUnique(PrimordialModel):
    ''' a base model where the name is not unique '''

    class Meta:
        abstract = True

    name          = models.CharField(max_length=512, unique=False)

class Tag(models.Model):
    '''
    any type of object can be given a search tag
    '''

    class Meta:
        app_label = 'main'

    name = models.CharField(max_length=512)

    def __unicode__(self):
        return unicode(self.name)

    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_TagsDetail, args=(self.pk,))

    @classmethod
    def can_user_add(cls, user, data):
        # anybody can make up tags
        return True

    @classmethod
    def can_user_read(cls, user, obj):
        # anybody can read tags, we won't show much detail other than the names
        return True


class AuditTrail(models.Model):
    '''
    changing any object records the change
    '''

    class Meta:
        app_label = 'main'

    resource_type = models.CharField(max_length=64)
    modified_by   = models.ForeignKey('auth.User', on_delete=SET_NULL, null=True, blank=True)
    delta         = models.TextField() # FIXME: switch to JSONField
    detail        = models.TextField()
    comment       = models.TextField()

    # FIXME: this looks like this should be a ManyToMany
    tag           = models.ForeignKey('Tag', on_delete=SET_NULL, null=True, blank=True)

class Organization(CommonModel):
    '''
    organizations are the basic unit of multi-tenancy divisions
    '''

    class Meta:
        app_label = 'main'

    users    = models.ManyToManyField('auth.User', blank=True, related_name='organizations')
    admins   = models.ManyToManyField('auth.User', blank=True, related_name='admin_of_organizations')
    projects = models.ManyToManyField('Project', blank=True, related_name='organizations')

    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_OrganizationsDetail, args=(self.pk,))

    @classmethod
    def can_user_delete(cls, user, obj):
        return user in obj.admins.all()

    @classmethod
    def can_user_administrate(cls, user, obj):
        # FIXME: super user checks should be higher up so we don't have to repeat them
        if user.is_superuser:
            return True
        if obj.created_by == user:
            return True
        rc = user in obj.admins.all()
        return rc

    @classmethod
    def can_user_read(cls, user, obj):
        return cls.can_user_administrate(user,obj) or user in obj.users.all()

    @classmethod
    def can_user_delete(cls, user, obj):
        return cls.can_user_administrate(user, obj)

    def __unicode__(self):
        return self.name

class Inventory(CommonModel):
    '''
    an inventory source contains lists and hosts.
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('inventories')
        unique_together = (("name", "organization"),)

    organization = models.ForeignKey(Organization, null=False, related_name='inventories')

    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_InventoryDetail, args=(self.pk,))

    @classmethod
    def _has_permission_types(cls, user, obj, allowed):
        if user.is_superuser:
            return True
        by_org_admin = obj.organization.admins.filter(pk = user.pk).count()
        by_team_permission = obj.permissions.filter(
            team__in = user.teams.all(),
            permission_type__in = allowed
        ).count()
        by_user_permission = obj.permissions.filter(
            user = user,
            permission_type__in = allowed
        ).count()

        result = (by_org_admin + by_team_permission + by_user_permission)
        return result > 0

    @classmethod
    def _has_any_inventory_permission_types(cls, user, allowed):
        '''
        rather than checking for a permission on a specific inventory, return whether we have
        permissions on any inventory.  This is primarily used to decide if the user can create
        host or group objects
        '''

        if user.is_superuser:
            return True
        by_org_admin = user.organizations.filter(
            admins__in = [ user ]
        ).count()
        by_team_permission = Permission.objects.filter(
            team__in = user.teams.all(),
            permission_type__in = allowed
        ).count()
        by_user_permission = user.permissions.filter(
            permission_type__in = allowed
        ).count()

        result = (by_org_admin + by_team_permission + by_user_permission)
        return result > 0

    @classmethod
    def can_user_add(cls, user, data):
        if not 'organization' in data:
            return True
        if user.is_superuser:
            return True
        if not user.is_superuser:
            org = Organization.objects.get(pk=data['organization'])
            if user in org.admins.all():
                return True
        return False

    @classmethod
    def can_user_administrate(cls, user, obj):
        return cls._has_permission_types(user, obj, PERMISSION_TYPES_ALLOWING_INVENTORY_ADMIN)

    @classmethod
    def can_user_attach(cls, user, obj, sub_obj, relationship_type):
        ''' whether you can add sub_obj to obj using the relationship type in a subobject view '''
        if not sub_obj.can_user_read(user, sub_obj):
            return False
        return cls._has_permission_types(user, obj, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)

    @classmethod
    def can_user_unattach(cls, user, obj, sub_obj, relationship):
        return cls._has_permission_types(user, obj, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)

    @classmethod
    def can_user_read(cls, user, obj):
        return cls._has_permission_types(user, obj, PERMISSION_TYPES_ALLOWING_INVENTORY_READ)

    @classmethod
    def can_user_delete(cls, user, obj):
        return cls._has_permission_types(user, obj, PERMISSION_TYPES_ALLOWING_INVENTORY_ADMIN)

class Host(CommonModelNameNotUnique):
    '''
    A managed node
    '''

    class Meta:
        app_label = 'main'
        unique_together = (("name", "inventory"),)

    variable_data  = models.OneToOneField('VariableData', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='host')
    inventory      = models.ForeignKey('Inventory', null=False, related_name='hosts')

    def __unicode__(self):
        return self.name

    @classmethod
    def can_user_read(cls, user, obj):
        return Inventory.can_user_read(user, obj.inventory)

    @classmethod
    def can_user_add(cls, user, data):
        if not 'inventory' in data:
            return False
        inventory = Inventory.objects.get(pk=data['inventory'])
        rc =  Inventory._has_permission_types(user, inventory, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)
        return rc

    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_HostsDetail, args=(self.pk,))

    # relationship to LaunchJobStatus
    # relationship to LaunchJobStatusEvent
    # last_job_status

class Group(CommonModelNameNotUnique):

    '''
    A group of managed nodes.  May belong to multiple groups
    '''

    class Meta:
        app_label = 'main'
        unique_together = (("name", "inventory"),)

    inventory     = models.ForeignKey('Inventory', null=False, related_name='groups')
    parents       = models.ManyToManyField('self', symmetrical=False, related_name='children', blank=True)
    variable_data = models.OneToOneField('VariableData', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='group')
    hosts         = models.ManyToManyField('Host', related_name='groups', blank=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def can_user_add(cls, user, data):
        if not 'inventory' in data:
            return False
        inventory = Inventory.objects.get(pk=data['inventory'])
        return Inventory._has_permission_types(user, inventory, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)


    @classmethod
    def can_user_administrate(cls, user, obj):
        # here this controls whether the user can attach subgroups
        return Inventory._has_permission_types(user, obj.inventory, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)

    @classmethod
    def can_user_read(cls, user, obj):
        return Inventory.can_user_read(user, obj.inventory)

    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_GroupsDetail, args=(self.pk,))

# FIXME: audit nullables
# FIXME: audit cascades

class VariableData(CommonModelNameNotUnique):
    '''
    A set of host or group variables
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('variable data')

    #host  = models.OneToOneField('Host', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='variable_data')
    #group = models.OneToOneField('Group', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='variable_data')
    data  = models.TextField() # FIXME: JsonField

    def __unicode__(self):
        return '%s = %s' % (self.name, self.data)

    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_VariableDetail, args=(self.pk,))

    @classmethod
    def can_user_read(cls, user, obj):
        ''' a user can be read if they are on the same team or can be administrated '''
        if obj.host is not None:
            return Inventory.can_user_read(user, obj.host.inventory)
        if obj.group is not None:
            return Inventory.can_user_read(user, obj.group.inventory)
        return False

class Credential(CommonModelNameNotUnique):
    '''
    A credential contains information about how to talk to a remote set of hosts
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''

    class Meta:
        app_label = 'main'

    user            = models.ForeignKey('auth.User', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')
    team            = models.ForeignKey('Team', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')

    # IF ssh_key_path is SET
    #
    # STAGE 1: SSH KEY SUPPORT
    #
    # ssh-agent bash &
    # save keyfile to tempdir in /var/tmp (permissions guarded)
    # ssh-add path-to-keydata
    # key could locked or unlocked, so use 'expect like' code to enter it at the prompt
    #    if key is locked:
    #       if ssh_key_unlock is provided provide key password
    #       if not provided, FAIL
    #
    # default_username if set corresponds to -u on ansible-playbook, if unset -u root
    #
    # STAGE 2:
    # OR if ssh_password is set instead, do not use SSH agent
    #    set ANSIBLE_SSH_PASSWORD
    #
    # STAGE 3:
    #
    # MICHAEL: modify ansible/ansible-playbook such that
    # if ANSIBLE_PASSWORD or ANSIBLE_SUDO_PASSWORD is set
    # you do not have to use --ask-pass and --ask-sudo-pass, so we don't have to do interactive
    # stuff with that.
    #
    # ansible-playbook foo.yml ...

    ssh_key_data     = models.TextField(blank=True, default='')
    ssh_key_unlock   = models.CharField(blank=True, default='', max_length=1024)
    default_username = models.CharField(blank=True, default='', max_length=1024)
    ssh_password     = models.CharField(blank=True, default='', max_length=1024)
    sudo_password    = models.CharField(blank=True, default='', max_length=1024)

    @classmethod
    def can_user_administrate(cls, user, obj):
        if user.is_superuser:
            return True
        if user == obj.user:
            return True

        if obj.user:
            if (obj.user.organizations.filter(admins__in = [user]).count()):
                return True
        if obj.team:
            if user in obj.team.organization.admins.all():
                return True
        return False

    @classmethod
    def can_user_delete(cls, user, obj):
        if obj.user is None and obj.team is None:
            # unassociated credentials may be marked deleted by anyone
            return True
        return cls.can_user_administrate(user,obj)

    @classmethod
    def can_user_read(cls, user, obj):
        ''' a user can be read if they are on the same team or can be administrated '''
        return cls.can_user_administrate(user, obj)

    @classmethod
    def can_user_add(cls, user, data):
        if user.is_superuser:
            return True
        if 'user' in data:
            user_obj = User.objects.get(pk=data['user'])
            return UserHelper.can_user_administrate(user, user_obj)
        if 'team' in data:
            team_obj = Team.objects.get(pk=data['team'])
            return Team.can_user_administrate(user, team_obj)

    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_CredentialsDetail, args=(self.pk,))

class Team(CommonModel):
    '''
    A team is a group of users that work on common projects.
    '''

    class Meta:
        app_label = 'main'

    projects        = models.ManyToManyField('Project', blank=True, related_name='teams')
    users           = models.ManyToManyField('auth.User', blank=True, related_name='teams')
    organization    = models.ForeignKey('Organization', blank=False, null=True, on_delete=SET_NULL, related_name='teams')

    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_TeamsDetail, args=(self.pk,))

    @classmethod
    def can_user_administrate(cls, user, obj):
        # FIXME -- audit when this is called explicitly, if any
        if user.is_superuser:
            return True
        if user in obj.organization.admins.all():
            return True
        return False

    @classmethod
    def can_user_read(cls, user, obj):
        if cls.can_user_administrate(user, obj):
            return True
        if obj.users.filter(pk__in = [ user.pk ]).count():
            return True
        return False

    @classmethod
    def can_user_add(cls, user, data):
        if user.is_superuser:
            return True
        if Organization.objects.filter(admins__in = [user]).count():
            # team assignment to organizations is handled elsewhere, this just creates
            # a blank team
            return True
        return False

    @classmethod
    def can_user_delete(cls, user, obj):
        return cls.can_user_administrate(user, obj)

class Project(CommonModel):
    '''
    A project represents a playbook git repo that can access a set of inventories
    '''

    # this is not part of the project, but managed with perms
    # inventories      = models.ManyToManyField('Inventory', blank=True, related_name='projects')

    local_repository = models.CharField(max_length=1024)
    scm_type         = models.CharField(max_length=64)
    default_playbook = models.CharField(max_length=1024)

    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_ProjectsDetail, args=(self.pk,))

    @classmethod
    def can_user_administrate(cls, user, obj):
        if user.is_superuser:
            return True
        if obj.created_by == user:
            return True
        organizations = Organization.objects.filter(admins__in = [ user ], projects__in = [ obj ])
        for org in organizations:
            if org in project.organizations():
                return True
        return False

    @classmethod
    def can_user_read(cls, user, obj):
        if cls.can_user_administrate(user,obj):
            return True
        # and also if I happen to be on a team inside the project
        # FIXME: add this too
        return False

    @classmethod
    def can_user_delete(cls, user, obj):
        return cls.can_user_administrate(user, obj)


class Permission(CommonModelNameNotUnique):
    '''
    A permission allows a user, project, or team to be able to use an inventory source.
    '''

    class Meta:
        app_label = 'main'

    # permissions are granted to either a user or a team:
    user            = models.ForeignKey('auth.User', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    team            = models.ForeignKey('Team', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')

    # to be used against a project or inventory (or a project and inventory in conjunction):
    project         = models.ForeignKey('Project', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    inventory       = models.ForeignKey('Inventory', null=True, on_delete=SET_NULL, related_name='permissions')

    # permission system explanation:
    #
    # for example, user A on inventory X has write permissions                 (PERM_INVENTORY_WRITE)
    #              team C on inventory X has read permissions                  (PERM_INVENTORY_READ)
    #              team C on inventory X and project Y has launch permissions  (PERM_INVENTORY_DEPLOY)
    #              team C on inventory X and project Z has dry run permissions (PERM_INVENTORY_CHECK)
    #
    # basically for launching, permissions can be awarded to the whole inventory source or just the inventory source
    # in context of a given project.
    #
    # the project parameter is not used when dealing with READ, WRITE, or ADMIN permissions.

    permission_type = models.CharField(max_length=64, choices=PERMISSION_TYPE_CHOICES)

    def __unicode__(self):
        return unicode("Permission(name=%s,ON(user=%s,team=%s),FOR(project=%s,inventory=%s,type=%s))" % (
            self.name,
            self.user,
            self.team,
            self.project,
            self.inventory,
            self.permission_type
        ))

# TODO: other job types (later)

class JobTemplate(CommonModel):
    '''
    A job template is a reusable job definition for applying a project (with
    playbook) to an inventory source with a given credential.
    '''

    class Meta:
        app_label = 'main'

    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='job_templates',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='job_templates',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        'Project',
        related_name='job_templates',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    user = models.ForeignKey(
        'auth.User',
        related_name='job_templates',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    # project has one default playbook but really should have a list of playbooks and flags ...

    # ssh-agent bash
    # ssh-add ... < key entry
    #
    # playbook in source control is already on the disk

    # we'll extend ansible core to have callback context like
    #    self.context.playbook
    #    self.context.runner
    #    and the callback will read the environment for ACOM_CELERY_JOB_ID or similar
    #    and log tons into the database

    # the ansible commander setup instructions will include installing the database logging callback
    # inventory script is going to need some way to load Django models
    #    it is documented on ansible.cc under API docs and takes two parameters
    #    --list
    #    -- host <hostname>

class Job(CommonModel):
    '''
    A job applies a project (with playbook) to an inventory source with a given
    credential.  It represents a single invocation of ansible-playbook with the
    given parameters.
    '''

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('running', _('Running')),
        ('successful', _('Successful')),
        ('failed', _('Failed')),
        ('error', _('Error')),
    ]

    class Meta:
        app_label = 'main'

    job_template = models.ForeignKey(
        'JobTemplate',
        related_name='jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        'Project',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    user = models.ForeignKey(
        'auth.User',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        editable=False,
    )
    result_stdout = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_stderr = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_traceback = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        editable=False,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='jobs',
        blank=True,
        editable=False,
        through='JobHostSummary',
    )

    @property
    def celery_task(self):
        try:
            if self.celery_task_id:
                return TaskMeta.objects.get(task_id=self.celery_task_id)
        except TaskMeta.DoesNotExist:
            pass

    def _run(self):
        from lib.main.tasks import run_job
        task_result = run_job.delay(self.pk)
        # The TaskMeta instance in the database isn't created until the worker
        # starts processing the task, so we can only store the task ID here.
        self.celery_task_id = task_result.task_id
        self.save(update_fields=['celery_task_id'])

    def save(self, *args, **kwargs):
        created = not bool(self.pk)
        super(Job, self).save(*args, **kwargs)
        # Create a new host summary for each host in the inventory.
        for host in self.inventory.hosts.all():
            # Due to the way the inventory script is called, hosts without a
            # group won't be included.
            if host.groups.count():
                self.job_host_summaries.get_or_create(host=host)
        # Start job running (but only if just created).
        if created and self.status == 'pending':
            self._run()

    @property
    def successful_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__ok__gt=0)

    @property
    def failed_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__failures__gt=0)

    @property
    def changed_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__changed__gt=0)

    @property
    def dark_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__dark__gt=0)

    @property
    def unreachable_hosts(self):
        return self.dark_hosts

    @property
    def skipped_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__skipped__gt=0)

    @property
    def processed_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__processed__gt=0)

class JobHostSummary(models.Model):
    '''
    Per-host statistics for each job.
    '''

    class Meta:
        unique_together = [('job', 'host')]
        verbose_name_plural = _('Job Host Summaries')
        ordering = ('-pk',)

    job = models.ForeignKey(
        'Job',
        related_name='job_host_summaries',
        on_delete=models.CASCADE,
    )
    host = models.ForeignKey('Host',
        related_name='job_host_summaries',
        on_delete=models.CASCADE,
    )

    changed = models.PositiveIntegerField(default=0)
    dark = models.PositiveIntegerField(default=0)
    failures = models.PositiveIntegerField(default=0)
    ok = models.PositiveIntegerField(default=0)
    processed = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return '%s changed=%d dark=%d failures=%d ok=%d processed=%d skipped=%s' % \
            (self.host.name, self.changed, self.dark, self.failures, self.ok,
             self.processed, self.skipped)

class JobEvent(models.Model):
    '''
    An event/message logged from the callback when running a job.
    '''

    EVENT_TYPES = [
        ('runner_on_failed', _('Runner on Failed')),
        ('runner_on_ok', _('Runner on OK')),
        ('runner_on_error', _('Runner on Error')),
        ('runner_on_skipped', _('Runner on Skipped')),
        ('runner_on_unreachable', _('Runner on Unreachable')),
        ('runner_on_no_hosts', _('Runner on No Hosts')),
        ('runner_on_async_poll', _('Runner on Async Poll')),
        ('runner_on_async_ok', _('Runner on Async OK')),
        ('runner_on_async_failed', _('Runner on Async Failed')),
        ('playbook_on_start', _('Playbook on Start')),
        ('playbook_on_notify', _('Playbook on Notify')),
        ('playbook_on_task_start', _('Playbook on Task Start')),
        ('playbook_on_vars_prompt', _('Playbook on Vars Prompt')),
        ('playbook_on_setup', _('Playbook on Setup')),
        ('playbook_on_import_for_host', _('Playbook on Import for Host')),
        ('playbook_on_not_import_for_host', _('Playbook on Not Import for Host')),
        ('playbook_on_play_start', _('Playbook on Play Start')),
        ('playbook_on_stats', _('Playbook on Stats')),
    ]

    class Meta:
        app_label = 'main'

    job = models.ForeignKey(
        'Job',
        related_name='job_events',
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )
    event = models.CharField(
        max_length=100,
        choices=EVENT_TYPES,
    )
    event_data = JSONField(
        blank=True,
        default='',
    )
    host = models.ForeignKey(
        'Host',
        related_name='job_events',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    def __unicode__(self):
        return u'%s @ %s' % (self.get_event_display(), self.created.isoformat())

    def save(self, *args, **kwargs):
        try:
            if not self.host and self.event_data.get('host', ''):
                self.host = self.job.inventory.hosts.get(name=self.event_data['host'])
        except (Host.DoesNotExist, AttributeError):
            pass
        super(JobEvent, self).save(*args, **kwargs)
        self.update_host_summary_from_stats()

    def update_host_summary_from_stats(self):
        if self.event != 'playbook_on_stats':
            return
        hostnames = set()
        try:
            for v in self.event_data.values():
                hostnames.update(v.keys())
        except AttributeError: # In case event_data or v isn't a dict.
            pass
        for hostname in hostnames:
            try:
                host = self.job.inventory.hosts.get(name=hostname)
            except Host.DoesNotExist:
                continue
            host_summary = self.job.job_host_summaries.get_or_create(host=host)[0]
            host_summary_changed = False
            for stat in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
                try:
                    value = self.event_data.get(stat, {}).get(hostname, 0)
                    if getattr(host_summary, stat) != value:
                        setattr(host_summary, stat, value)
                        host_summary_changed = True
                except AttributeError: # in case event_data[stat] isn't a dict.
                    pass
            if host_summary_changed:
                host_summary.save()

# TODO: reporting (MPD)

@receiver(post_save, sender=User)
def create_auth_token_for_user(sender, **kwargs):
    instance = kwargs.get('instance', None)
    if instance:
        try:
            Token.objects.get_or_create(user=instance)
        except DatabaseError:
            pass    # Only fails when creating a new superuser from syncdb on a
                    # new database (before migrate has been called).
