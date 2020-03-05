gcp_http_lb
=========

This role helps you set up a Google Cloud Load Balancer.

Requirements
------------

- requests Python library
- googleauth Python library

Role Variables
--------------

```
  gcp_http_lb_backend: the selflink for the backend that this load balancer will be supporting
  gcp_project: the name of your gcp project
  service_account_file: the path to your service account JSON file
```

Example Playbook
----------------

    - hosts: local
      vars:
        gcp_http_lb_backend: projects/project/zones/us-central1-c/instanceGroups/my-instance-group
      roles:
         - role: gcp_http_lb

License
-------

GPLv3

Author Information
------------------

Google Inc.
