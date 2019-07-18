## Collections Support

AWX supports Ansible collections by appending the directories specified in `AWX_ANSIBLE_COLLECTIONS_PATHS` 
to the environment variable `ANSIBLE_COLLECTIONS_PATHS`. The default value of `AWX_ANSIBLE_COLLECTIONS_PATHS`
contains `/var/lib/awx/collections`. It is recommended that place your collections that you wish to call in 
your playbooks into this path.
