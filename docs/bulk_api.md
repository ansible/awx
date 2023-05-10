# Bulk API Overview

Bulk API endpoints allows to perform bulk operations in single web request. There are currently following bulk api actions:
- /api/v2/bulk/job_launch
- /api/v2/bulk/host_create

Making individual API calls in rapid succession or at high concurrency can overwhelm AWX's ability to serve web requests. When the application's ability to serve is exausted, clients often receive 504 timeout errors.

 Allowing the client combine actions into fewer requests allows for launching more jobs or adding more hosts with fewer requests and less time without exauhsting Controller's ability to serve requests, making excessive and repetitive database queries, or using excessive database connections (each web request opens a seperate database connection).

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

The maximum number of jobs allowed to be launched in one bulk launch is controlled by the setting `BULK_JOB_MAX_LAUNCH`.

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

*Note:* The `instance_groups` relationship is not supported for node-level prompts, unlike `"credentials"` in the above example, and will be ignored if provided. See OPTIONS for `/api/v2/bulk/job_launch/` for what fields are accepted at the workflow and node level, as that is the ultimate source of truth to determine what fields the API will accept.

### RBAC For Bulk Job Launch

#### Who can bulk launch?
Anyone who is logged in can view the launch point. In order to launch a unified_job_template, you need to have either `update` or `execute` depending on the type of unified job (job template, project update, etc).

Launching using the bulk endpoint results in a workflow job being launched. For auditing purposes, in general we require to assign an organization to the resulting workflow. The logic for assigning this organization is as follows:

- Superusers may assign any organization or none. If they do not assign one, they will be the only user able to see the parent workflow.
- Users that are members of exactly 1 organization do not need to specify an organization, as their single organization will be used to assign to the resulting Workflow
- Users that are members of multiple organizations must specify the organization to assign to the resulting workflow. If they do not specify, an error will be returned indicating this requirement.

Example of specifying the organization:

    {
        "name": "Bulk Job Launch with org specified",
        "jobs": [
            {"unified_job_template": 12},
            {"unified_job_template": 13}
        ],
        "organization": 2
    }

#### Who can see bulk jobs that have been run?
System admins and Organization admins will see Bulk Jobs in the workflow jobs list and the unified jobs list. They can additionally see these individual workflow jobs.

Regular users can only see the individual workflow jobs that were launched by their bulk job launch. These jobs do not appear in the unified jobs list, nor do they show in the workflow jobs list. This is important because the response to a bulk job launch includes a link to the parent workflow job.

## Bulk Host Create

Provides feature in the API that allows a single web request to create multiple hosts in an inventory.  

Following is an example of a post request at the /api/v2/bulk/host_create:


    {
        "inventory": 1,
        "hosts": [{"name": "host1", "variables": "ansible_connection: local"}, {"name": "host2"}, {"name": "host3"}, {"name": "host4"}, {"name": "host5"}, {"name": "host6"}]
    }


The above will add 6 hosts in the inventory.

The maximum number of hosts allowed to be added is controlled by the setting `BULK_HOST_MAX_CREATE`. The default is 100 hosts. Additionally, nginx limits the maximum payload size, which is very likely when posting a large number of hosts in one request with variable data associated with them. The maximum payload size is 1MB unless overridden in your nginx config.
