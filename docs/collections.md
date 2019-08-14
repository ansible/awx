## Collections

AWX supports using Ansible collections.
This section will give ways to use collections in job runs.

### Project Collections Requirements

If you specify a collections requirements file in SCM at `collections/requirements.yml`,
then AWX will install collections in that file in the implicit project sync
before a job run. The invocation is:

```
ansible-galaxy collection install -r requirements.yml -p <job tmp location>
```

Example of tmp directory where job is running:

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

### Global Collections Path

AWX appends the directories specified in `AWX_ANSIBLE_COLLECTIONS_PATHS`
to the environment variable `ANSIBLE_COLLECTIONS_PATHS`. The default value of `AWX_ANSIBLE_COLLECTIONS_PATHS`
contains `/var/lib/awx/collections`. It is recommended that place your collections that you wish to call in
your playbooks into this path.
