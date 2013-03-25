# (c) 2013, AnsibleWorks, Michael DeHaan <michael@ansibleworks.com>
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.


from django.db import models
from django.db.models import CASCADE, SET_NULL, PROTECT
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import exceptions

# TODO: jobs and events model TBD
# TODO: reporting model TBD

PERM_INVENTORY_READ   = 'read'
PERM_INVENTORY_WRITE  = 'write'
PERM_INVENTORY_DEPLOY = 'run'
PERM_INVENTORY_CHECK  = 'check'

JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, _('Run')),
    (PERM_INVENTORY_CHECK, _('Check')),
]

PERMISSION_TYPES = [
    PERM_INVENTORY_READ,
    PERM_INVENTORY_WRITE,
    PERM_INVENTORY_DEPLOY,
    PERM_INVENTORY_CHECK,
]

PERMISSION_TYPES_ALLOWING_INVENTORY_READ = PERMISSION_TYPES

PERMISSION_TYPE_CHOICES = [
    (PERM_INVENTORY_READ, _('Read Inventory')),
    (PERM_INVENTORY_WRITE, _('Write Inventory')),
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
        matching_orgs = len(set(obj.organizations.all()) & set(user.admin_of_organizations.all()))
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
        matching_orgs = len(set(obj.organizations.all()) & set(user.admin_of_organizations.all()))
        return matching_orgs


class CommonModel(models.Model):
    '''
    common model for all object types that have these standard fields
    '''

    class Meta:
        abstract = True

    name          = models.CharField(max_length=512, unique=True)
    description   = models.TextField(blank=True, default='')
    created_by    = models.ForeignKey('auth.User', on_delete=SET_NULL, null=True, related_name='%s(class)s_created') # not blank=False on purpose for admin!
    creation_date = models.DateField(auto_now_add=True)
    tags          = models.ManyToManyField('Tag', related_name='%(class)s_by_tag', blank=True)
    audit_trail   = models.ManyToManyField('AuditTrail', related_name='%(class)s_by_audit_trail', blank=True)
    active        = models.BooleanField(default=True)

    def __unicode__(self):
        return unicode(self.name)

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
    def can_user_add(cls, user):
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
    def can_user_add(cls, user):
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

    organization = models.ForeignKey(Organization, null=True, on_delete=SET_NULL, related_name='inventories')
    
    def get_absolute_url(self):
        import lib.urls
        return reverse(lib.urls.views_InventoryDetail, args=(self.pk,))

    def __unicode__(self):
        if self.organization:
            return u'%s (%s)' % (self.name, self.organization)
        else:
            return self.name

class Host(CommonModel):
    '''
    A managed node
    '''

    class Meta:
        app_label = 'main'

    inventory = models.ForeignKey('Inventory', null=True, on_delete=SET_NULL, related_name='hosts')

    def __unicode__(self):
        return self.name

class Group(CommonModel):
    '''
    A group of managed nodes.  May belong to multiple groups
    '''

    class Meta:
        app_label = 'main'

    inventory = models.ForeignKey('Inventory', null=True, on_delete=SET_NULL, related_name='groups')
    parents   = models.ManyToManyField('self', symmetrical=False, related_name='children', blank=True)
    hosts     = models.ManyToManyField('Host', related_name='groups', blank=True)

    def __unicode__(self):
        return self.name

# FIXME: audit nullables
# FIXME: audit cascades

class VariableData(CommonModel):
    '''
    A set of host or group variables
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('variable data')

    host  = models.ForeignKey('Host', null=True, default=None, blank=True, on_delete=CASCADE, related_name='variable_data')
    group = models.ForeignKey('Group', null=True, default=None, blank=True, on_delete=CASCADE, related_name='variable_data')
    data  = models.TextField() # FIXME: JsonField

    def __unicode__(self):
        return '%s = %s' % (self.name, self.data)

class Credential(CommonModel):
    '''
    A credential contains information about how to talk to a remote set of hosts
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''

    class Meta:
        app_label = 'main'

    user            = models.ForeignKey('auth.User', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')
    project         = models.ForeignKey('Project', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')
    team            = models.ForeignKey('Team', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')

    ssh_key_path    = models.CharField(blank=True, default='', max_length=4096)
    ssh_key_data    = models.TextField(blank=True, default='') # later
    ssh_key_unlock  = models.CharField(blank=True, default='', max_length=1024)
    ssh_password    = models.CharField(blank=True, default='', max_length=1024)
    sudo_password   = models.CharField(blank=True, default='', max_length=1024)


class Team(CommonModel):
    '''
    A team is a group of users that work on common projects.
    '''

    class Meta:
        app_label = 'main'

    projects        = models.ManyToManyField('Project', blank=True, related_name='teams')
    users           = models.ManyToManyField('auth.User', blank=True, related_name='teams')
    organizations   = models.ManyToManyField('Organization', related_name='teams')

class Project(CommonModel):
    '''
    A project represents a playbook git repo that can access a set of inventories
    '''

    inventories      = models.ManyToManyField('Inventory', blank=True, related_name='projects')
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


class Permission(CommonModel):
    '''
    A permission allows a user, project, or team to be able to use an inventory source.
    '''

    class Meta:
        app_label = 'main'

    user            = models.ForeignKey('auth.User', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    project         = models.ForeignKey('Project', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    team            = models.ForeignKey('Team', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    inventory       = models.ForeignKey('Inventory', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    permission_type = models.CharField(max_length=64, choices=PERMISSION_TYPE_CHOICES)

# TODO: other job types (later)

class LaunchJob(CommonModel):
    '''
    a launch job is a request to apply a project to an inventory source with a given credential
    '''

    class Meta:
        app_label = 'main'

    inventory      = models.ForeignKey('Inventory', on_delete=SET_NULL, null=True, default=None, blank=True, related_name='launch_jobs')
    credential     = models.ForeignKey('Credential', on_delete=SET_NULL, null=True, default=None, blank=True, related_name='launch_jobs')
    project        = models.ForeignKey('Project', on_delete=SET_NULL, null=True, default=None, blank=True, related_name='launch_jobs')
    user           = models.ForeignKey('auth.User', on_delete=SET_NULL, null=True, default=None, blank=True, related_name='launch_jobs')

    # JOB_TYPE_CHOICES are a subset of PERMISSION_TYPE_CHOICES
    job_type       = models.CharField(max_length=64, choices=JOB_TYPE_CHOICES)

    def start(self):
        from lib.main.tasks import run_launch_job
        return run_launch_job.delay(self.pk)

    # project has one default playbook but really should have a list of playbooks and flags ...


    # ENOUGH_TO_RUN_DJANGO=foo ACOM_INVENTORY_ID=<pk> ansible-playbook <path to project selected playbook.yml> -i ansible-commander-inventory.py
    #                                                                            ^-- this is a hard coded path
    # ssh-agent bash
    # ssh-add ... < key entry
    #
    # inventory script I can write, and will use ACOM_INVENTORY_ID
    #
    #
    # playbook in source control is already on the disk

    # job_type:
    #   run, check -- enough for now, more initially
    #      if check, add "--check" to parameters

    # we'll extend ansible core to have callback context like
    #    self.context.playbook
    #    self.context.runner
    #    and the callback will read the environment for ACOM_CELERY_JOB_ID or similar
    #    and log tons into the database

    # we'll also log stdout/stderr somewhere for debugging

    # the ansible commander setup instructions will include installing the database logging callback
    # inventory script is going to need some way to load Django models
    #    it is documented on ansible.cc under API docs and takes two parameters
    #    --list
    #    -- host <hostname>

    # posting the LaunchJob should return some type of resource that we can check for status
    # that all the log data will use as a Foreign Key

# TODO: Events

class LaunchJobStatus(CommonModel):

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('launch job statuses')

    launch_job     = models.ForeignKey('LaunchJob', null=True, on_delete=SET_NULL, related_name='launch_job_statuses')
    status         = models.IntegerField()
    result_data    = models.TextField()


# TODO: reporting (MPD)


