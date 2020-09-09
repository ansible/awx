## Collections

AWX supports the use of Ansible Collections. This section will give ways to use Collections in job runs.

### Project Collections Requirements

If you specify a collections requirements file in SCM at `collections/requirements.yml`,
then AWX will install collections from that file to a special cache folder in project updates.
Before a job runs, the roles and/or collections will be copied from the special
cache folder to the job temporary folder.

The invocation looks like:

```
ansible-galaxy collection install -r requirements.yml -p <project cache location>/requirements_collections
```

Example of the resultant job `tmp` directory where job is running:

```
├── project
│   ├── ansible.cfg
│   └── debug.yml
├── requirements_collections
│   └── ansible_collections
│       └── collection_namespace
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

### Cache Folder Mechanics

Every time a project is updated as a "check" job
(via `/api/v2/projects/N/update/` or by a schedule, workflow, etc.),
the roles and collections are downloaded and saved to the project's content cache.
In other words, the cache is invalidated every time a project is updated.
That means that the `ansible-galaxy` commands are ran to download content
even if the project revision does not change in the course of the update.

Project updates all initially target a staging directory at a path like:

```
/var/lib/awx/projects/.__awx_cache/_42__project_name/stage
```

After the update finishes, the task logic will decide what id to associate
with the content downloaded.
Then the folder will be renamed from "stage" to the cache id.
For instance, if the cache id is determined to be 63:

```
/var/lib/awx/projects/.__awx_cache/_42__project_name/63
```

The cache may be updated by project syncs (the "run" type) which happen before
job runs. It will populate the cache id set by the last "check" type update.

### Galaxy Server Selection

For details on how Galaxy servers are configured in Ansible in general see:

https://docs.ansible.com/ansible/devel/user_guide/collections_using.html
(if "devel" link goes stale in the future, it is for Ansible 2.9)

You can specify a list of zero or more servers to download roles and
collections from for AWX Project Updates.  This is done by associating Galaxy
credentials (in sequential order) via the API at
`/api/v2/organizations/N/galaxy_credentials/`.  Authentication
via an API token is optional (i.e., https://galaxy.ansible.com/), but other
content sources (such as Red Hat Ansible Automation Hub) require proper
configuration of the Auth URL and Token.

If no credentials are defined at this endpoint for an Organization, then roles and
collections will *not* be installed based on requirements.yml for Project Updates
in that Organization.

Even when these settings are enabled, this can still be bypassed for a specific
requirement by using the `source:` option, as described in Ansible documentation.
