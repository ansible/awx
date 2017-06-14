## Instructions on using an isolated node

The building of the isolated node is done in the `make docker-compose-build`
target. Its image uses a different tag from the tools_tower container.

Given that the images are built, you can run the combined docker compose target. This uses
the base `docker-compose.yml` with modifications found in `docker-isolated-override.yml`.
You will still need to give COMPOSE_TAG with whatever your intended
base branch is. For example:

```bash
make docker-isolated COMPOSE_TAG=devel
```

This will automatically exchange the keys in order for the `tools_tower_1`
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

## Development Testing Notes

### Test the SSH connection between containers

While the environment is running, you can test the connection like so:

```bash
docker exec -i -t tools_tower_1 /bin/bash
```

Inside the context of that container:

```bash
ssh root@isolated
```

(note: awx user has been deprecated)

This should give a shell to the `tools_isolated_1` container, as the
`tools_tower_1` container sees it.

### Start the playbook service

The following command would run the playbook for job 57.

```bash
systemctl start playbook@57.service
```

