## Instructions on using an isolated node

The building of the isolated node is done in the `make docker-compose-build`
target. Its image uses a different tag from the tools_awx container.

Given that the images are built, you can run the combined docker compose target. This uses
the base `docker-compose.yml` with modifications found in `docker-isolated-override.yml`.
You will still need to give COMPOSE_TAG with whatever your intended
base branch is. For example:

```bash
make docker-isolated COMPOSE_TAG=devel
```

This will automatically exchange the keys in order for the `tools_awx_1`
container to access the `tools_isolated_1` container over ssh.
After that, it will bring up all the containers like the normal docker-compose
workflow.

### Running a job on the Isolated Node

Create a job template that runs normally. Add the id of the instance
group named `thepentagon` to the JT's instance groups. To do this, POST
the id (probably id=2) to `/api/v2/job_templates/N/instance_groups/`.
After that, run the job template.

The models are automatically created when running the Makefile target,
and they are structured as follows:

    +-------+     +-------------+
    | tower |<----+ thepentagon |
    +-------+     +-------------+
        ^                ^
        |                |
        |                |
    +---+---+      +-----+----+
    | tower |      | isolated |
    +-------+      +----------+

The `controller` for the group "thepentagon" and all hosts therein is
determined by a ForeignKey within the instance group.

### Run a playbook

In order to run an isolated job, associate the instance group `thepentagon` with
a job template, inventory, or organization, then run a job that derives from
that resource. You should be able to confirm success by inspecting the
`instance_group` of the job.

#### Advanced Manual Testing

If you want to run a job manually inside of the isolated container with this
tooling, you need a private data directory. Normal isolated job runs will
clean up their private data directory, but you can temporarily disable this
by disabling some parts of the cleanup_isolated.yml playbook.

Example location of a private data directory:

`/tmp/awx_29_OM6Mnx/`

The following command would run the playbook corresponding to that job.

```bash
ansible-runner start /tmp/awx_29_OM6Mnx/ -p some_playbook.yml
```

Other ansible-runner commands include `start`, `is-alive`, and `stop`.
