## Process Isolation Overview

In older version of Ansible Tower we used a system called `proot` to isolate tower job processes from the rest of the system.

For Tower 3.1 and later we have switched to using `bubblewrap` which is a much lighter weight and maintained process isolation system.

Tower 3.5 forward uses the process isolation feature in ansible runner to achieve process isolation.

### Activating Process Isolation

By default `bubblewrap` is enabled, this can be turned off via Tower Config or from a tower settings file:

    AWX_PROOT_ENABLED = False
    
Process isolation, when enabled, will be used for the following Job Types:

* Job Templates - Launching jobs from regular job templates
* Ad-hoc Commands - Launching ad-hoc commands against one or more hosts in inventory

### Tunables

Process Isolation will, by default, hide the following directories from the tasks mentioned above:

* /etc/tower - To prevent exposing Tower configuration
* /var/lib/awx - With the exception of the current project being used (for regular job templates)
* /var/log
* /tmp (or whatever the system temp dir is) - With the exception of the processes's own temp files

If there is other information on the system that is sensitive and should be hidden that can be added via the Tower Configuration Screen
or by updating the following entry in a tower settings file:

    AWX_PROOT_HIDE_PATHS = ['/list/of/', '/paths']
    
If there are any directories that should specifically be exposed that can be set in a similar way:

    AWX_PROOT_SHOW_PATHS = ['/list/of/', '/paths']
    
By default the system will use the system's tmp dir (/tmp by default) as it's staging area. This can be changed:

    AWX_PROOT_BASE_PATH = "/opt/tmp"
