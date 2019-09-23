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
