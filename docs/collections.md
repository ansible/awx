## Collections

AWX supports the use of Ansible Collections. This section will give ways to use Collections in job runs.

### Project Collections Requirements

If you specify a Collections requirements file in SCM at `collections/requirements.yml`,
then AWX will install Collections from that file in the implicit project sync
before a job run. The invocation looks like:

```
ansible-galaxy collection install -r requirements.yml -p <job tmp location>/requirements_collections
```

Example of the resultant `tmp` directory where job is running:

```
├── project
│   ├── ansible.cfg
│   └── debug.yml
├── requirements_collections
│   └── ansible_collections
│       └── username
│           └── collection_name
│               ├── FILES.json
│               ├── MANIFEST.json
│               ├── README.md
│               ├── roles
│               │   ├── role_in_collection_name
│               │   │   ├── defaults
│               │   │   │   └── main.yml
│               │   │   ├── tasks
│               │   │   │   └── main.yml
│               │   │   └── templates
│               │   │       └── stuff.j2
│               └── tests
│                   └── main.yml
├── requirements_roles
│   └── username.role_name
│       ├── defaults
│       │   └── main.yml
│       ├── meta
│       │   └── main.yml
│       ├── README.md
│       ├── tasks
│       │   ├── main.yml
│       │   └── some_role.yml
│       ├── templates
│       │   └── stuff.j2
│       └── vars
│           └── Archlinux.yml
└── tmp_6wod58k

```

### Galaxy Server Selection

Ansible core default settings will download collections from the public
Galaxy server at `https://galaxy.ansible.com`. For details on
how Galaxy servers are configured in Ansible in general see:

https://docs.ansible.com/ansible/devel/user_guide/collections_using.html
(if "devel" link goes stale in the future, it is for Ansible 2.9)

You can set a different server to be the primary Galaxy server to download
roles and collections from in AWX project updates.
This is done via the setting `PRIMARY_GALAXY_URL` and similar
`PRIMARY_GALAXY_xxxx` settings for authentication.

If the `PRIMARY_GALAXY_URL` setting is not blank, then the server list is defined
to be `primary_galaxy,galaxy`. The `primary_galaxy` server definition uses the URL
from those settings, as well as username, password, and/or token and auth_url if applicable.
the `galaxy` server definition uses public Galaxy (`https://galaxy.ansible.com`)
with no authentication.

This configuration causes requirements to be downloaded from the user-specified
primary galaxy server if they are available there. If a requirement is
not available from the primary galaxy server, then it will fallback to
downloading it from the public Galaxy server.

Even when these settings are enabled, this can still be bypassed for a specific
requirement by using the `source:` option, as described in Ansible documentation.
