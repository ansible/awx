
User default view -- buttons appear/disappear based on permissions
/web/home

   [TEAMS] -- all teams with permissions shown here
   t1         [ view ]  [ edit ]
   t2         [ view ]  [ edit ]
   [+ create team]                

   [PROJECTS] -- all projects with permissions shown here
   () p1      [ view ]  [ edit ] 
   () p2      [ view ]  [ edit ] 
   () p3      [ view ]  [ edit ]  
   [+ create project]
    
   [INVENTORIES] -- all inventories with permissions shown here
   () i1      [ view ]  [ edit ]
   () i2      [ view ]  [ edit ] 
   [+ create inventory]

   [CREDENTIALS] -- team and user creds shown here
   () c1      [ view ]  [ edit ]
   () c2      [ view ]  [ edit ] 
   [+ user cred]

Org Page Edit/View
/web/org/#{org_id}

   [ users listing/adding/deleting admin widget ] -- can add/see users if org admin 
   [ projects listing/adding/deleting admin widget ]  -- can add/see if org admin

Team Page Edit/View
/web/team/#{team_id}

    [ users listing/adding/deleting admin widget ] -- can add if org admin, can see if on team
    [ credentials listing/adding/deleting admin widget ] -- can create/edit team creds here if on team
    [ projects listing/adding/deleting admin widget ] -- can add existing proj to team if org admin, see if on team


Project Page Edit/View
/web/project/#{project_id}

    see what teams share this project, links to them
    [ view/edit properties ] 
    
    [ PUSH ] [ CHECK ] buttons
    must select an inventory source    
    must select a credential the user or team has for that source
    in order to enable

    clicking button gets you a link to the page in events

Events Page
/web/events/

     you can see all the events on things you have inventory
     access for.

Jobs Page
/web/jobs

     you can see all the pages you have inventory access for
     
Inventory Page Edit/View
/web/inventory/#{inventory_id}

    [ groups listing/adding/deleting widget ]
    [ hosts listing/adding/deleting widget ] 
    [ links on each host to log data ]

Individual edit pages

    what you can do varies by access level

/web/hosts/N
/web/groups/N
/web/users/N

/web/projects/N

    viewer and editor as appropriate
    for filesystem tree
    will presumably NOT be super-graphical/editable in additional round
    Cloud9 IDE?



`
