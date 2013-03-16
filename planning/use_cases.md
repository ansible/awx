About
=====

This was an early doc of some of the things we want to be able to do.
As database and plans change, this is not neccessarily our most up
to date plan, but leaving this here for reference.

Roles
=====

a user can be:

Regular User
Site Admin
Org Admin
User on a Team
  
Regular User
============

* can login
* can logout
* can change some user info but not their username (can change pass)

Site Admin
==========

* probably installed the platform from a playbook before using the tool
* can make user accounts 
* can promote users to site admin (or remove that)
* can add existing users to any organization
* is automatically an admin of all orgs
 
Org Admin
=========

* can create users (they are auto assigned to the org)
* can kick users out of the org
* can promote users to org admin or demote them
* can create an inventory source
* can share an inventory source with a team or user with set permissions
  - ability to edit
  - ability to push
  - ability to run in check mode
  - ability to view
  - ability to see log data
* can create a project in the org
* can create a team in the org
* can associate a project with one or more teams in the org
* can add users to projects or take them away

A Project
=========
* has a git repository path (previously unused or used exactly once in DB)
* may have credentials

A Credential
============
* ssh key location (new or only used once)
* ssh unlock
* password
* sudo password
* pem file location (new or only used once)

A User
======
* can login
* can logout
* may have credentials
* can push to any inventory source (or check, view, etc) if they have permission on that source via a team membership, directly, an org membership, etc.  The links to do so are found in the context of the project.  A user may acquire permissions on an inventory source via multiple routes.  Permissions are usually locked around a particular project.
* can view logs on hosts if they have similar permissions on that inv. source



