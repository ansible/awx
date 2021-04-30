# Tower Ansible Collection

[comment]: # (*******************************************************)
[comment]: # (*                                                     *)
[comment]: # (*             WARNING                                 *)
[comment]: # (*                                                     *)
[comment]: # (*  This file is templated and not to be               *)
[comment]: # (*  edited directly! Instead modify:                   *)
[comment]: # (*  tools/roles/template_galaxy/templates/README.md.j2 *)
[comment]: # (*                                                     *)
[comment]: # (*  Changes to the base README.md file are refreshed   *)
[comment]: # (*  upon build of the collection                       *)
[comment]: # (*******************************************************)

This Ansible collection allows for easy interaction with an Ansible Tower server via Ansible playbooks.

This source for this collection lives in the `awx_collection` folder inside of the
AWX source.
The previous home for this collection was inside the folder [lib/ansible/modules/web_infrastructure/ansible_tower](https://github.com/ansible/ansible/tree/stable-2.9/lib/ansible/modules/web_infrastructure/ansible_tower) in the Ansible repo,
as well as other places for the inventory plugin, module utils, and
doc fragment.

## Building and Installing

This collection should be installed from [Content Hub](https://cloud.redhat.com/ansible/automation-hub/ansible/tower/)

## Running

Non-deprecated modules in this collection have no Python requirements, but
may require the official [AWX CLI](https://docs.ansible.com/ansible-tower/latest/html/towercli/index.html)
in the future. The `DOCUMENTATION` for each module will report this.

You can specify authentication by a combination of either:

 - host, username, password
 - host, OAuth2 token

The OAuth2 token is the preferred method. You can obtain a token via the
AWX CLI [login](https://docs.ansible.com/ansible-tower/latest/html/towercli/reference.html#awx-login)
command.

These can be specified via (from highest to lowest precedence):

 - direct module parameters
 - environment variables (most useful when running against localhost)
 - a config file path specified by the `tower_config_file` parameter
 - a config file at `~/.tower_cli.cfg`
 - a config file at `/etc/tower/tower_cli.cfg`

Config file syntax looks like this:

```
[general]
host = https://localhost:8043
verify_ssl = true
oauth_token = LEdCpKVKc4znzffcpQL5vLG8oyeku6
```

## Release and Upgrade Notes

Notable releases of the `ansible.controller` collection:

 - 3.7.0 initial release

The following notes are changes that may require changes to playbooks:

 - The module tower_notification was renamed tower_notification_template. In ansible >= 2.10 there is a seemless redirect. Ansible 2.9 does not respect the redirect.
 - When a project is created, it will wait for the update/sync to finish by default; this can be turned off with the `wait` parameter, if desired.
 - Creating a "scan" type job template is no longer supported.
 - Specifying a custom certificate via the `TOWER_CERTIFICATE` environment variable no longer works.
 - Type changes of variable fields:

   - `extra_vars` in the `tower_job_launch` module worked with a `list` previously, but now only works with a `dict` type
   - `extra_vars` in the `tower_workflow_job_template` module worked with a `string` previously but now expects a `dict`
   - When the `extra_vars` parameter is used with the `tower_job_launch` module, the launch will fail unless `ask_extra_vars` or `survey_enabled` is explicitly set to `True` on the Job Template
   - The `variables` parameter in the `tower_group`, `tower_host` and `tower_inventory` modules now expects a `dict` type and no longer supports the use of `@` syntax for a file


 - Type changes of other types of fields:

   - `inputs` or `injectors` in the `tower_credential_type` module worked with a string previously but now expects a `dict`
   - `schema` in the `tower_workflow_job_template` module worked with a `string` previously but not expects a `list` of `dict`s

 - `tower_group` used to also service inventory sources, but this functionality has been removed from this module; use `tower_inventory_source` instead.
 - Specified `tower_config` file used to handle `k=v` pairs on a single line; this is no longer supported. Please use a file formatted as `yaml`, `json` or `ini` only.
 - Some return values (e.g., `credential_type`) have been removed. Use of `id` is recommended.
 - `tower_job_template` no longer supports the deprecated `extra_vars_path` parameter, please use `extra_vars` with the lookup plugin to replace this functionality.
 - The `notification_configuration` parameter of `tower_notification_template` has changed from a string to a dict. Please use the `lookup` plugin to read an existing file into a dict.
 - `tower_credential` no longer supports passing a file name to ssh_key_data.
 - The HipChat `notification_type` has been removed and can no longer be created using the `tower_notification_template` module.


## Licensing

All content in this folder is licensed under the same license as Ansible,
which is the same as license that applied before the split into an
independent collection.
