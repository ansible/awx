#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 -U postgres <<-EOSQL
    CREATE USER galaxy_ng;
    CREATE DATABASE galaxy_ng;
    GRANT ALL PRIVILEGES ON DATABASE galaxy_ng TO galaxy_ng;
EOSQL
