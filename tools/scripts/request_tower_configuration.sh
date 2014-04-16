#!/bin/bash

usage() {
  echo -e "Requests server configuration from Ansible Tower\n"
  echo "Usage: $0 <server address>[:server port] <host config key> <job template id>"
  echo "Example: $0 example.towerhost.net 44d7507f2ead49af5fca80aa18fd24bc 38"
  exit 1
}

[ $# -lt 3 ] && usage

retry_attempts=10
attempt=0
while [[ $attempt -lt $retry_attempts ]]
do
  status_code=`curl -s -i --data "host_config_key=$2" http://$1/api/v1/job_templates/$3/callback/ | head -n 1 | awk '{print $2}'`
  if [[ $status_code == 202 ]]
    then
    exit 0
  fi
  attempt=$(( attempt + 1 ))
  echo "${status_code} received... retrying in 1 minute. (Attempt ${attempt})"
  sleep 60
done
exit 1
