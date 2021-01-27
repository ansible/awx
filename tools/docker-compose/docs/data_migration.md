# Migrating Data from Local Docker

If you are migrating data from a Local Docker installation (17.0.1 and prior), you can 
migrate your data to the development environment via the migrate.yml playbook, or by using the manual steps described below.  

> Note: This will also convert your postgresql bind-mount into a docker volume.

### Migrate data with migrate.yml

If you had a custom pgdocker or awxcompose location, you will need to set the `postgres_data_dir` and `old_docker_compose_dir` variables. 

1. Run the [migrate playbook](./ansible/migrate.yml) to migrate your data to the new postgresql container and convert the data directory to a volume mount.
```bash
$ ansible-playbook migrate.yml -e "migrate_local_docker=true" -e "postgres_data_dir=~/.awx/pgdocker" -e "old_docker_compose_dir=~/.awx/awxcompose"
```

2. Change directory to the top of your awx checkout and start your containers
```bash
$ make docker-compose
```

3. After ensuring your data has been successfully migrated, you may delete your old data directory (typically stored at `~/.awx/pgdocker`). 


### Migrating data manually

1. With Local Docker still running, perform a pg_dumpall:
> Note: If Local Docker is no longer running
`docker-compose -f ~/.awx/awxcompose/docker-compose.yml up postgres`

  ```bash
  $ docker-compose -f ~/.awx/awxcompose/docker-compose.yml exec postgres pg_dumpall -U awx > awx_dump.sql
  ```

2. Remove all local docker containers (specifically awx_postgres)
```bash
$ docker -f rm awx_postgres
```

3. Template the new docker-compose.yml
```bash
$ ansible-playbook -i tools/ansible/inventory tools/ansible/sources.yml
```

4. Start a container with a volume (using the new tools/docker-compose/_sources/docker-compose.yml)
```bash
$ docker-compose -f ../docker-compose/_sources/docker-compose.yml up postgres
```

5. Restore to new `awx_postgres`
```bash
$ docker-compose -f ../docker-compose/_sources/docker-compose.yml exec -T postgres psql -U awx -d awx -p 5432 < awx_dump.sql
```

6. Run the docker-compose.yml to start the containers
```bash
$ docker-compose -f ../docker-compose/_sources/docker-compose.yml up task
```

7. Check to ensure your data migration was successful, then you can delete your the `awx_dump.sql` backup and your old data directory.  
