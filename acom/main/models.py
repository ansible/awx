from django.db import models

# TODO: split into seperate files?
# TODO: smart objects discussion
# TODO: jobs and events model
# TODO: how to link up with Django user auth
# TODO: general schema review/organization

class CommonModel(models.Model):
    ''' 
    common model for all object types that have these standard fields 
    '''

    class Meta:
        abstract = True

    name          = models.TextField()
    description   = models.TextField()
    creation_date = models.DateField()
    tags          = models.ManyToManyField('Tag')  
  
class Tag(CommonModel):
   ''' 
   any type of object can be given a search tag 
   '''

   class Meta:
        db_table = 'tags'

   id   = models.AutoField(primary_key=True)
   name = models.TextField()
 
 
class AuditTrail(CommonModel):
    ''' 
    changing any object records the change 
    '''
 
    class Meta:
        db_table = 'audit_trails'

    id            = models.AutoField(primary_key=True)
    resource_type = models.TextField()
    modified_by   = models.ForeignKey('User')
    delta         = models.ForeignKey('Delta')
    detail        = models.TextField()
    comment       = models.TextField()
    tag           = models.ForeignKey('Tag')

class Organization(CommonModel):
    ''' 
    organizations are the basic unit of multi-tenancy divisions 
    '''    

    class Meta:
        db_table = 'organizations'

    id     = models.AutoField(primary_key=True)
    users  = models.ManyToManyField('User')
    admins = models.ManyToManyField('User')

class Inventory(CommonModel):
    ''' 
    an inventory source contains lists and hosts.
    '''
  
    class Meta:
        db_table = 'inventory'

    id                = models.AutoField(primary_key=True)
    organization      = models.ForeignKey(Organization)    
    sync_script_path  = models.TextField() # for future use

class Host(CommonModel):
    '''
    A managed node
    '''

    class Meta:
        db_table = 'hosts'

    id        = models.AutoField(primary_key=True)
    inventory = models.ForeignKey('Inventory')
    

class Group(CommonModel):
    '''
    A group of managed nodes.  May belong to multiple groups
    '''

    class Meta:
        db_table = 'groups'

    id        = models.AutoField(primary_key=True)
    inventory = models.ForeignKey('Inventory')
    parents   = models.ManyToManyField('Group') # ? 

class InventoryVariable(CommonModel):
    '''
    A variable
    '''  

    class Meta:
        db_table = 'inventory_variables'

    id    = models.AutoField(primary_key=True)
    host  = models.ForeignKey('Host')
    group = models.ForeignKey('Group')
    key   = models.TextField()
    value = models.TextField()

class User(CommonModel):
    '''
    Basic user class
    '''

    # FIXME: how to integrate with Django auth?

    class Meta:
        db_table = 'users'

    id            = models.AutoField(primary_key=True)
    organization  = models.ManyToManyField('Organization')
    team          = models.ManyToManyField('Team')
    credentials   = models.ManyToManyField('Credential')

class Credential(CommonModel):
    '''
    A credential contains information about how to talk to a remote set of hosts
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''

    
    class Meta:
        db_table = 'credentials'

    id              = models.AutoField(primary_key=True)
    user            = models.ForeignKey('User')
    project         = models.ForeignKey('Project')
    team            = models.ForeignKey('Team')
    ssh_key_path    = models.TextField()
    ssh_key_data    = models.TextField() # later
    ssh_key_unlock  = models.TextField()
    ssh_password    = models.TextField()
    sudo_password   = models.TextField()

class Team(CommonModel):
    '''
    A team is a group of users that work on common projects.
    '''
    
    class Meta:
        db_table = 'teams'

    id              = models.AutoField(primary_key=True)
    projects        = models.ManyToManyField('Project')
    credentials     = models.ManyToManyField('Credential')
    users           = models.ManyToManyField('User')
    organization    = models.ManyToManyField('Organization')

class Project(CommonModel):
    '''  
    A project represents a playbook git repo that can access a set of inventories
    '''   
 
    class Meta:
        db_table = 'projects'

    id               = models.AutoField(primary_key=True)
    credentials      = models.ManyToManyField('Credential')
    inventories      = models.ManyToManyField('Inventory')
    local_repository = models.TextField()
    scm_type         = models.TextField()
    default_playbook = models.TextField()

class Permission(CommonModel):
    '''
    A permission allows a user, project, or team to be able to use an inventory source.
    '''

    class Meta:
        db_table = 'permissions'

    id              = models.AutoField(primary_key=True)
    user            = models.ForeignKey('User')
    project         = models.ForeignKey('Project')
    team            = models.ForeignKey('Team')
    # ... others? 

# TODO: Jobs

class LaunchJob(CommonModel):
    ''' a launch job is a request to apply a project to an inventory source with a given credential'

    inventory      = models.ForeignKey('Inventory')
    credential     = models.ForeignKey('Credential')
    project        = models.ForeignKey('Project')
    user           = models.ForeignKey('User')
    job_type       = models.TextField()
    event          = models.ForeignKey('Event')    

# TODO: Events


