# Migrating Data from Local Docker

If you are migrating data from a Local Docker installation (17.0.1 and prior) to AWX 18.0 or higher, you can
migrate your data to the development environment via the migrate.yml playbook.

> Note: This will also convert your postgresql bind-mount into a docker volume.

### Migrate data with migrate.yml

First, in the  [`inventory` file](../inventory), set your `pg_password`, `broadcast_websocket_secret`, `secret_key`, and any other settings you need for your deployment.  **Make sure you use the same values from the `inventory` file in your existing pre-18.0.0 Docker deployment.**

If you used a custom pgdocker or awxcompose location, you will need to set the `postgres_data_dir` and `old_docker_compose_dir` variables.

1. Run the [migrate playbook](../ansible/migrate.yml) to migrate your data to the new postgresql container and convert the data directory to a volume mount.
```bash
$ ansible-playbook  -i tools/docker-compose/inventory tools/docker-compose/ansible/migrate.yml -e "migrate_local_docker=true" -e "postgres_data_dir=~/.awx/pgdocker" -e "old_docker_compose_dir=~/.awx/awxcompose"
```

2. Change directory to the top of your awx checkout, and follow the [development environment installation instructions](../README.md) to start your containers:
```bash
$ make docker-compose-build
$ make docker-compose
$ make ui
```

3. After ensuring your data has been successfully migrated, you may delete your old data directory (typically stored at `~/.awx/pgdocker`).

4.  Note that after migration, the development environment will be available at https://localhost:8043/ (not http://localhost).
