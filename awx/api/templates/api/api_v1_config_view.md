{% ifmeth GET %}
# Site configuration settings and general information

Make a GET request to this resource to retrieve the configuration containing
the following fields (some fields may not be visible to all users):

* `project_base_dir`: Path on the server where projects and playbooks are \
  stored.
* `project_local_paths`: List of directories beneath `project_base_dir` to
  use when creating/editing a project.
* `time_zone`: The configured time zone for the server.
* `license_info`: Information about the current license.
* `version`: Version of Ansible Tower package installed.
* `eula`: The current End-User License Agreement
{% endifmeth %}

{% ifmeth POST %}
# Install or update an existing license

(_New in Ansible Tower 2.0.0_) Make a POST request to this resource as a super
user to install or update the existing license.  The license data itself can
be POSTed as a normal json data structure.

(_New in Ansible Tower 2.1.1_) The POST must include a `eula_accepted` boolean
element indicating acceptance of the End-User License Agreement.
{% endifmeth %}

{% ifmeth DELETE %}
# Delete an existing license

(_New in Ansible Tower 2.0.0_) Make a DELETE request to this resource as a super
user to delete the existing license
{% endifmeth %}
