API Overview
============

The following is a start to an API document.  It is just a sketch and may evolve as we build things out.

Versioning and Semantics
========================

* All results will either be JSON lists or hashes.
* Only new fields will be added.
* Fields will not be removed.
* URLs are all discoverable, so discover them.  Hardcode to prevent against changes, though we'll try not to move anything.
* If you have a 'href' value in JSON, the last part after the last "/", if a number, corresponds to a database ID.
* No IDs will be returned bare, that is, just as integers.
* Objects in list results will be summarized and not include all field info.  Usually just an href + type + name + description.  Sometimes more.
* All IDs are "big serial" type.
* All JSON returns should have a 'type' in easy structure saying the object type.

Hashes will typically have:

   {
       'href' : 'http://...'  # the resource URL
       'name' : 'Fred'        # the name of the object (non-unique)
       'description' : '...'  # some free text describing the object
       'tags' : [             # some optional freeform tags
          'asdf', 'jkl'
       ]
       'audit_trail': href,
   }

API discovery
=============

The root of the API here will be denoted as '/', though for all practical purposes it could be anything.
Getting '/' will return the URLs of other endpoints that are useful.  There is no security to get '/',
though everything else requires a username+password.  If you first get "/" you can see all of the API URLs
you can use and walk them.

/

   GET -- List all of the available API endpoints to enable service discoverability

   {
       'organizations' : '/orgs',
       'users'         : '/users',
       'projects'      : '/projects',
       # etc
   }

Authentication
==============

An initial user will be created in the database.

URLs require authentication (AuthN) in basic username:password format.

Tokens also supported (/login).  TBA.

Authorization varies by URL (see use_cases.md for roles)

Sync scripts will be created to pull from AD and so on.

Pagination
==========

API calls for lists will be paginated.

The default start index will be 0 and the default number of records per page will be 99.

Affix the following the URL to specify differently.

?

Audit Records
=============

Audit trail records are recorded for most edit types.

/audit

   GET    --  lists all the audit records the user has access to
   
/audit/#{audit_id}

   GET

   {
      'href'          : /audit/12345
      'id'            : ...
      'record_type'   : ...  # what type of audit trail, for example 'user'
      'resource'      : href
      'date'          : ...
      'modified_by'   : href
      'delta'         : # for put operations, any fields that are changed, for creation, any added.  RAW JSON.
      'detail'        : some string message set by the system
      'comment'       : [], comments supplied by the user, if any
      'tags'          : []  # tags the user may have added, like 'investigate'
   }

   PUT -- requires org admin

   allows modification, but only to set tag fields and add comments.  Previous comments
   are not edited, so the last comment in the list only will be saved (if different)


Organizations
=============

/orgs

   GET     -- List all of the available organizations the user is in, or all, if site admin

   [
      { 
         'href'        : '...',
         'id'          : 12345,
         'name'        : 'Finance',
         'description' : '...'          

      }, ...
   ]

   POST    -- Add a new organization

/orgs/#{org_id}

   GET    -- Get the details of an organization
   PUT    -- Updates an organization
   DELETE -- Expires an organization

/orgs/#{org_id}/users/

   GET    -- Lists users in an organization
   POST   -- Add a user record to the organization

/orgs/#{org_id}/users/#{user_id}

/orgs/#{org_id}/admins/

   GET    -- list the admins
   POST   -- make a user an admin

/orgs/#{org_id}/admins/{#user_id}

   DELETE -- demote an admin

Users
=====

/users/
   GET - list all users I can see based on my permissions
/users/#{user_id}/
   GET - show the specific user if I have permission
   DELETE - expires the user but doesn't delete them, requires org admin access
/users/#{user_id}/credentials/
   GET - show the credentials set on the user
   other ops through the /credentials/#{cred_id} URL
/users/#{user_id}/permissions/
   GET - see what permissions the user has assigned, but can't edit here
   other ops through the /permissions/#{cred_id} URL
/users/#{user_id}/teams/
   GET - see what teams the user has defined, but not editable here
   other ops through the /teams/#{team_id} URL
/users/#{user_id}/projects/
   GET - see what projects the user is a part of, but you can get this through the indiv teams too
   other ops through the /projects/#{project_id} URL

Teams
=====

/teams/
   GET -- shows all the teams the user is on, or if admin/org admin, all teams
   POST -- make a new team
/teams/#{team_id}/users/
   GET -- show users on the team
   POST -- add an existing user to the team
/teams/#{team_id}/users/#{user_id}
   DELETE -- kick the user off the team
/teams/#{team_id}/projects/
   GET -- shows all the projects on the team if you can see the team
   POST -- share a project with a team
   other ops through /projects/#{project_id}
/teams/#{team_id}/users/
   GET -- shows all uses on the team if you can see the team
   other ops through /users/#{user_id}
/teams/#{team_id}/credentials
   GET -- gets the credential records of the team, recommended for close friends, otherwise upload to user acct
   other ops through 
/teams/#{team_id}/permissions/
   GET -- show all permissions that were assigned to the team

Projects
========

/projects/
   GET -- show all the projects the user can see  
   POST -- make a new project
/projects/#{project_id}
   GET -- show the project if someone is allowed to read the info
/projects/#{project_id}/inventory/
   GET -- get the inventory records assigned to this project
/projects/#{project_id}/inventory/#{inventory_id}
   DELETE -- remove inventory source from project
/projects/#{project_id}/users/
   GET -- users on the project
/projects/#{project_id}/users/#{user_id}
   DELETE(id) -- remove user from project
   POST -- add user to project if allowed
/project/#{project_id}/credentials/
   GET -- show credentials on project
/project/#{project_id}/credentials/#{credential_id}
   DELETE -- remove credentials
/project/#{project_id}/permissions
   GET -- see all the permissions on the project
   delete permissions through /permissions/#{permission_id}

Inventory
=========

/inventory/
    GET -- see all the inventory sources the user is allowed to see
/inventory/#{inventory_id}
    GET    -- see the specific source
    DELETE -- expire the inventory source if sufficient permission
/inventory/#{inventory_id}/hosts
    GET -- see hosts
    POST -- add hosts and associate
/inventory/#{inventory_id}/groups
    GET -- see groups
    POST -- add groups and associate
/inventory/#{inventory_id}/permissions
    GET -- see all permissions for everyone granted on the inventory source, if you have access

Hosts
=====

Note: must be created via inventory source

/hosts/
/hosts/#{host_id}
    GET -- see the host record
/hosts/#{host_id}/vars
    GET -- see the host vars
    PUT -- edit them
/hosts/#{host_id}/groups/
    GET -- see the groups
    POST -- add some more groups to the host

Groups
======

/groups/
    GET -- see all the groups the user can see
/groups/#{group_id}
    GET -- see the specific group
/groups/#{group_id}/vars
    GET -- see the vars
    PUT -- edit them
/groups/#{group_id}/hosts/
    GET -- see the hosts in the group
    POST -- add existing host records to the group
/groups/#{group_id}/subgroups/
    GET -- see the direct subgroups
    POST - add an existing group to the group as a subgroup

Permissions
=====================

/permissions/
    GET -- see all the permissions that map to any of the users contexts (??)

/permissions/#{permission_id}

    {
        href: href,
        project: href,
        team: href,
        user: href,
        inventory: href,
        allowed: [
           'edit', 'push', 'check', 'view', 'logs'
        ]
    }

    GET
    DELETE


Jobs
====

/jobs/

   GET  -- get a list of active jobs you can see
   POST -- add a job, rather specific as to what this is...

/jobs/#{job_id} 

   GET    -- get info about a job
   DELETE -- remove a job

The most obvious job you will want to do is to deploy a project against an inventory source.

   POST /jobs/

   {
       'inventory_id' : href,
       'project_id'   : href,
       'ansible_tags' : [],
       'job_type'     : href,
   }

   and you'll get back an event ID you can poll

   {
       'id'    : href,
       'type'  : event,
   }

Where job_types are in the database too and public:

/job_types/

As are job status types

/job_status_types/

Events
======

/events/

   GET    -- root of the event service

/events/jobs/
   
   GET    -- get all events for the job

/events/jobs/#{job_id}
  
   GET    -- event info

   {
        id:    'href'
        type:  'event'
        status: 'running'
   }

/host_status/
/hosts_status/#{host_id}/status
   
   GET    -- get all statuses for the host

   {
       id:        href
       date:      date
       host_id:   href
       success:   true
       event_id:  href
   }
   


/host_log_records/#{host_log_id}

   GET 

   {
      id:       href
      host_id:  href
      event_id: href
      success:  true/false
      skipped:  true/false
      failed:   true/false
      dark:     true/false
   }



Reporting
=========

/reporting/  <- incoming messages go here

   POST -- accepts remote reporting events.  Requires a host id.



