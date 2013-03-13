from django.db import models

# TODO: jobs and events model
# TODO: how to link up with Django user auth
# TODO: general schema review/organization
# TODO: audit cascade behavior and defaults
# TODO: set related names

# SET_NULL = models.SET_NULL
# PROTECT  = models.PROTECT

class CommonModel(models.Model):
    ''' 
    common model for all object types that have these standard fields 
    '''

    class Meta:
        abstract = True

    name          = models.TextField()
    description   = models.TextField()
    creation_date = models.DateField()
    tags          = models.ManyToManyField('Tag', related_name='%(class)s_tags') 
    audit_trail   = models.ManyToManyField('AuditTrail', related_name='%(class)s_audit_trails')
 
class Tag(models.Model):
    ''' 
    any type of object can be given a search tag 
    '''

    name = models.TextField()
 
 
class AuditTrail(CommonModel):
    ''' 
    changing any object records the change 
    '''
 
    resource_type = models.TextField()
    modified_by   = models.ForeignKey('User')
    delta         = models.TextField() # FIXME: switch to JSONField
    detail        = models.TextField()
    comment       = models.TextField()
    tag           = models.ForeignKey('Tag')

class Organization(CommonModel):
    ''' 
    organizations are the basic unit of multi-tenancy divisions 
    '''    

    users    = models.ManyToManyField('User', related_name='organizations')
    admins   = models.ManyToManyField('User', related_name='admin_of_organizations')
    projects = models.ManyToManyField('Project', related_name='organizations')

class Inventory(CommonModel):
    ''' 
    an inventory source contains lists and hosts.
    '''
  
    organization = models.ForeignKey(Organization, related_name='inventories')    

class Host(CommonModel):
    '''
    A managed node
    '''

    inventory = models.ForeignKey('Inventory', related_name='hosts')
    

class Group(CommonModel):
    '''
    A group of managed nodes.  May belong to multiple groups
    '''

    inventory = models.ForeignKey('Inventory', related_name='groups')
    parents   = models.ManyToManyField('self', related_name='children') 

# FIXME: audit nullables
# FIXME: audit cascades

class VariableData(CommonModel):
    '''
    A set of host or group variables
    '''  

    host  = models.ForeignKey('Host', null=True, default=None, blank=True, related_name='variable_data')
    group = models.ForeignKey('Group', null=True, default=None, blank=True, related_name='variable_data')
    data  = models.TextField() # FIXME: JsonField

class User(CommonModel):
    '''
    Basic user class
    '''

    # FIXME: how to integrate with Django auth?

    auth_user     = models.OneToOneField('auth.User', related_name='application_user')

class Credential(CommonModel):
    '''
    A credential contains information about how to talk to a remote set of hosts
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''

    user            = models.ForeignKey('User', null=True, default=None, blank=True, related_name='credentials')
    project         = models.ForeignKey('Project', null=True, default=None, blank=True, related_name='credentials')
    team            = models.ForeignKey('Team', null=True, default=None, blank=True, related_name='credentials')

    ssh_key_path    = models.TextField(blank=True, default='')
    ssh_key_data    = models.TextField(blank=True, default='') # later
    ssh_key_unlock  = models.TextField(blank=True, default='')
    ssh_password    = models.TextField(blank=True, default='')
    sudo_password   = models.TextField(blank=True, default='')
    

class Team(CommonModel):
    '''
    A team is a group of users that work on common projects.
    '''
    
    projects        = models.ManyToManyField('Project', related_name='teams')
    users           = models.ManyToManyField('User', related_name='teams')
    organization    = models.ManyToManyField('Organization', related_name='teams')

class Project(CommonModel):
    '''  
    A project represents a playbook git repo that can access a set of inventories
    '''   
 
    inventories      = models.ManyToManyField('Inventory', related_name='projects')
    local_repository = models.TextField()
    scm_type         = models.TextField()
    default_playbook = models.TextField()

class Permission(CommonModel):
    '''
    A permission allows a user, project, or team to be able to use an inventory source.
    '''

    user            = models.ForeignKey('User', related_name='permissions')
    project         = models.ForeignKey('Project', related_name='permissions')
    team            = models.ForeignKey('Team', related_name='permissions')
    job_type        = models.TextField()

# TODO: other job types (later)

class LaunchJob(CommonModel):
    ''' 
    a launch job is a request to apply a project to an inventory source with a given credential 
    '''

    inventory      = models.ForeignKey('Inventory', null=True, default=None, blank=True, related_name='launch_jobs')
    credential     = models.ForeignKey('Credential', null=True, default=None, blank=True, related_name='launch_jobs')
    project        = models.ForeignKey('Project', null=True, default=None, blank=True, related_name='launch_jobs')
    user           = models.ForeignKey('User', null=True, default=None, blank=True, related_name='launch_jobs')
    job_type       = models.TextField()
    
 

# TODO: Events

class LaunchJobStatus(CommonModel):

    launch_job     = models.ForeignKey('LaunchJob', related_name='launch_job_statuses')
    status         = models.IntegerField()
    result_data    = models.TextField()
     

# TODO: reporting (MPD)


