#!/bin/bash

usage() {
  echo -e "Retry callback attempt if we don't receive a 202 response from the Tower API\n"
  echo "Usage: $0 <server address>[:server port] <host config key> <job template id>"
  exit 1
}

[ $# -lt 3 ] && usage

retry_attempts=5
attempt=0
while [[ $attempt < $retry_attempts ]]
do
  status_code=`curl -s -i --data "host_config_key=$2" http://$1/api/v1/job_templates/$3/callback/ | head -n 1 | awk '{print $2}'`
  if [[ $status_code == 202 ]]
    then
    exit 0
  fi
  attempt=$(( attempt + 1 ))
  echo "${status_code} received... retrying."
  sleep 5
done
exit 1
