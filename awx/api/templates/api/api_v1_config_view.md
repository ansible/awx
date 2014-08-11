Site configuration settings and general information.

Make a GET request to this resource to retrieve the configuration containing
the following fields (some fields may not be visible to all users):

* `project_base_dir`: Path on the server where projects and playbooks are \
  stored.
* `project_local_paths`: List of directories beneath `project_base_dir` to
  use when creating/editing a project.
* `time_zone`: The configured time zone for the server.
* `license_info`: Information about the current license.
* `version`: Version of Ansible Tower (AWX) package installed.

Make a POST request to this resource as a super user to install or update the
existing license.  The license data itself can be POSTed as a normal json data
structure.