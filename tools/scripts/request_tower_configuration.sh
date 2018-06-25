#!/bin/bash

fatal() {
  if [ -n "${2}" ]; then
    echo -e "Error: ${2}"
  fi
  exit ${1}
}

usage() {
cat << EOF
Usage: $0 <options>

Request server configuration from Ansible Tower.

OPTIONS:
   -h      Show this message
   -s      Tower server (e.g. https://tower.example.com) (required)
   -k      Allow insecure SSL connections and transfers
   -c      Host config key (required)
   -t      Job template ID (required)
   -e      Extra variables
EOF
}

# Initialize variables
INSECURE=""

# Parse arguments
while getopts “hks:c:t:s:e:” OPTION
do
  case ${OPTION} in
    h)
      usage
      exit 1
      ;;
    s)
      TOWER_SERVER=${OPTARG}
      ;;
    k)
      INSECURE="-k"
      ;;
    c)
      HOST_CFG_KEY=${OPTARG}
      ;;
    t)
      TEMPLATE_ID=${OPTARG}
      ;;
    e)
      EXTRA_VARS=${OPTARG}
      ;;
    ?)
      usage
      exit
      ;;
  esac
done

# Validate required arguments
test -z ${TOWER_SERVER} && fatal 1 "Missing required -s argument"
# Make sure TOWER_SERVER starts with http:// or https://
[[ "${TOWER_SERVER}" =~ ^https?:// ]] || fatal 1 "Tower server must begin with http:// or https://"
test -z ${HOST_CFG_KEY} && fatal 1 "Missing required -c argument"
test -z ${TEMPLATE_ID} && fatal 1 "Missing required -t argument"

# Generate curl --data parameter
if [ -n "${EXTRA_VARS}" ]; then
  CURL_DATA="{\"host_config_key\": \"${HOST_CFG_KEY}\", \"extra_vars\": \"${EXTRA_VARS}\"}"
else
  CURL_DATA="{\"host_config_key\": \"${HOST_CFG_KEY}\"}"
fi

# Success on any 2xx status received, failure on only 404 status received, retry any other status every min for up to 10 min
RETRY_ATTEMPTS=10
ATTEMPT=0
while [[ $ATTEMPT -lt $RETRY_ATTEMPTS ]]
do
  set -o pipefail
  HTTP_STATUS=$(curl ${INSECURE} -s -i -X POST -H 'Content-Type:application/json' --data "$CURL_DATA" ${TOWER_SERVER}/api/v2/job_templates/${TEMPLATE_ID}/callback/ 2>&1 | head -n1 | awk '{print $2}')
  CURL_RC=$?
  if [ ${CURL_RC} -ne 0 ]; then
    fatal ${CURL_RC} "curl exited with ${CURL_RC}, halting."
  fi

  # Extract http status code
  if [[ ${HTTP_STATUS} =~ ^2[0-9]+$ ]]; then
    echo "Success: ${HTTP_STATUS} received."
    break
  elif [[ ${HTTP_STATUS} =~ ^404$ ]]; then
    fatal 1 "Failed: ${HTTP_STATUS} received, encountered problem, halting."
  else
    ATTEMPT=$((ATTEMPT + 1))
    echo "Failed: ${HTTP_STATUS} received, executing retry #${ATTEMPT} in 1 minute."
    sleep 60
  fi
done
