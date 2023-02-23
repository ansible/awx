# Bulk API Overview

Bulk API endpoints allows to perform bulk operations in single web request. There are currently following bulk api actions:
- /api/v2/bulk/job_launch
- /api/v2/bulk/host_create

## Bulk Job Launch

Provides feature in the API that allows a single web request to achieve multiple job launches. It creates a workflow job with individual jobs as nodes within the workflow job. It also supports providing promptable fields like inventory, credential etc.

Following is an example of a post request at the /api/v2/bulk/job_launch

    {
        "name": "Bulk Job Launch",
        "jobs": [
            {"unified_job_template": 7},
            {"unified_job_template": 8},
            {"unified_job_template": 9}
        ]
    }

The above will launch a workflow job with 3 nodes in it. 

**Important Note: A bulk job launched by a normal user will not be visible in the jobs section of the UI, although the individual jobs within a bulk job can be seen there.** 

If the job template has fields marked as prompt on launch, those can be provided for each job in the bulk job launch as well:

    {
        "name": "Bulk Job Launch",
        "jobs": [
            {"unified_job_template": 11, "limit": "kansas", "credentials": [1], "inventory": 1}
        ]
    }

In the above example `job template 11` has limit, credentials and inventory marked as prompt on launch and those are provided as parameters to the job.

Prompted field value can also be provided at the top level. For example:

    {
        "name": "Bulk Job Launch",
        "jobs": [
            {"unified_job_template": 11, "limit": "kansas", "credentials": [1]},
            {"unified_job_template": 12},
            {"unified_job_template": 13}
        ],
        "inventory": 2
    }

In the above example, `inventory: 2` will get used for the job templates (11, 12 and 13) in which inventory is marked as prompt of launch.

## Bulk Host Create

Provides feature in the API that allows a single web request to create multiple hosts in an inventory.  

Following is an example of a post request at the /api/v2/bulk/host_create:


    {
        "inventory": 1,
        "hosts": [{"name": "host1", "variables": "ansible_connection: local"}, {"name": "host2"}, {"name": "host3"}, {"name": "host4"}, {"name": "host5"}, {"name": "host6"}]
    }


The above will add 6 hosts in the inventory.