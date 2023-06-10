#!/bin/bash

cat <<EOF | PGPASSWORD=${POSTGRES_PASSWORD} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
-- Verify or create "db_monitor" user and permissions
do \$\$
declare
    dbm_oid oid := null::oid;
begin
    select to_regrole('db_monitor')
      into dbm_oid;

    if dbm_oid is null
    then
        create role db_monitor
          with login
               noinherit
               nocreatedb
               nosuperuser
               nocreaterole
               noreplication
               encrypted password '${POSTGRES_PASSWORD}';

        revoke all on all tables in schema public from db_monitor;
        revoke all on schema public from db_monitor;
        grant usage on schema public to db_monitor;
        grant pg_read_all_stats to db_monitor;
    end if;
end;
\$\$ language plpgsql;
EOF
