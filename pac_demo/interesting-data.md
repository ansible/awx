all user modifiable flat properties
id:
created: datetime
created_by: <scheduled will be created_by None>
    username:
    id:
    email:
    is_superuser
<!-- credentials:[{id: ,name, type}, ...] -->
execution_environments: []
    id:
    name:
    image:
    pull:
extra_vars:
extra_vars_dict:
forks:
count(hosts):
instance_group:
    id:
    name:
    capacity:
    jobs_running:
    jobs_total:
    max_concurrent_jobs:
    max_forks:
inventory
    id:
    name:
    description:
    total_hosts:
    total_groups:
    inventory_sources: []
        id:
        name:
        type:
        kind: ?
    <TODO figure out what identify a constructed inventory>
job_template:
    id:
    name:
    type
job_type:
job_type_name:
launch_type:
name:
limit:
launched_by: ?
organization:
    name:
    id:
playbook:
project:
    name:
    id:
    scm_*:
    status:
scm_branch =
scm_revision =
workflow_job_id
workflow_node_id
workflow_job_template: ?


<only provide info that's serialized to the API>
