#!/usr/bin/env bash

# this is what to run locally to test functionality before
# mirroring content into AWX
ansible-playbook -i localhost, test_job_run.yml --vault-id=awx@password_file