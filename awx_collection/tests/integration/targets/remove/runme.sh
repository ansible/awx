#!/usr/bin/env bash

ANSIBLE_NOCOWS=1 ansible-playbook -i inventory test_remove.yml