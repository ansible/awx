# Bulk API Overview

Bulk API endpoints allows to perform bulk operations in single web request. There are currently following bulk api actions:
- /api/v2/bulk/job_launch
- /api/v2/bulk/host_create

## Bulk Job Launch

Provides feature in the API that allows a single web request to achieve multiple job launches. It creates a workflow job with individual jobs as nodes within the workflow job. It also supports providing promptable fields like inventory, credential etc.

Following is an example of a post request at the /api/v2/bulk/job_launch

```commandline
{
"name": "Bulk Job Launch",
"jobs": [
   {"unified_job_template": 7, "identifier":"foo", "limit": "kansas", "credentials": [1]},
   {"unified_job_template": 8, "identifier":"bar", "inventory": 1, "execution_environment": 3},
   {"unified_job_template": 9}
]
}
```

The above will launch a workflow job with 3 nodes in it. 

## Bulk Host Create

Provides feature in the API that allows a single web request to create multiple hosts in an inventory.  

Following is an example of a post request at the /api/v2/bulk/host_create:

```commandline
{
    "inventory": 1,
    "hosts": [{"name": "host1", "variables": "ansible_connection: local"}, {"name": "host2"}, {"name": "host3"}, {"name": "host4"}, {"name": "host5"}, {"name": "host6"}]
}
```

The above will add 6 hosts in the inventory.