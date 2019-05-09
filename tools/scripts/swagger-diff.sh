#! /usr/bin/env sh
gem install swagger-diff
curl -s "https://docs.ansible.com/ansible-tower/latest/html/towerapi/_static/swagger.json" -o /tmp/before
curl -s "https://s3.amazonaws.com/awx-public-ci-files/schema.json" -o /tmp/after
swagger-diff -i /tmp/before /tmp/after | more
