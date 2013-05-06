Mockups
=======

Goals/priority:

   Organizations
   Inventory
      Groups
      Hosts
      Subgroup
      Host variable
      Group variable
   Jobs and Job Results
   Credentials 
   Projects
   Teams
   Permissions

Later/Roadmap:

   Rich Editing

Just conceptual stuff prior to using Balsamiq.

   Login
 
   username: 
   password:

When log in, menu options:

  organizations
  projects
  teams
  credentials

Organization tab:

  [if admin, plus sign for add ? ]
  org1    [ if admin, delete ]
  org2
  org3 

Organizations detail:

  [ see all properties ]
  [ click to edit some of them if admin ]

  [ if org admin, + project to organization ]
  [               + add a user ]
  [               + add more admins ]

Projects details:

   (projects are created from the organization detail page)

Teams:
  
   add users / remove users

Users:

   add remove/users

Credentials:

Permissions:

Jobs:

Inventory View:

   | Groups
   +--+   Subgroup   <----------------- click on this
      +----- subgroup

   see hosts in group that was selected above, (directly?)

   MPD: may need to add a way to see all child hosts of a given group in API
   /api/v1/groups/N/all_hosts
   if no group is selected, use /api/v1/hosts/

   [   Group selector ]  [ edit link ] [ delete link (if no kids?) ]

   [   Host list      ]  [ edit link ] [ delete link ] 


   tree of   list of
   GROUPS |  HOSTS
     x    |  asdf
      x   |  jkl
     x    |  foo
       x  |
       x  |
 


