3.3.0
=====
* Allow relaunching jobs on a subset of hosts, by status.[[#219](https://github.com/ansible/awx/issues/219)]
* Added `ask_variables_on_launch` to workflow JTs.[[#497](https://github.com/ansible/awx/issues/497)]
* Added `diff_mode` and `verbosity` fields to WFJT nodes.[[#555](https://github.com/ansible/awx/issues/555)]
* Block creation of schedules when variables not allowed are given.
  Block similar cases for WFJT nodes.[[#478](https://github.com/ansible/awx/issues/478)]
* Changed WFJT node `credential` to many-to-many `credentials`.
* Saved Launch-time configurations feature - added WFJT node promptable fields to schedules,
  added `extra_data` to WFJT nodes, added "schedule this job" endpoint.
  [[#169](https://github.com/ansible/awx/issues/169)]
* Switch from `credential`, `vault_credential`, and `extra_credentials` fields to
  single `credentials` relationship, allow multiple vault credentials [[#352](https://github.com/ansible/awx/issues/352)].
* Make inventory parsing errors fatal, and only enable the `script`
  inventory plugin for job runs and vendored inventory
  updates[[#864](https://github.com/ansible/awx/issues/864)]
* Add related `credentials` endpoint for inventory updates to be more internally
  consistent with job templates, model changes for [[#277](https://github.com/ansible/awx/issues/277)]
* Removed `TOWER_HOST` as a default environment variable in job running environment
  due to conflict with tower credential type. Playbook authors should replace their
  use with `AWX_HOST`. [[#1727](https://github.com/ansible/awx/issues/1727)]
* Boolean fields for custom credential types will now always default extra_vars and
  environment variables to `False` when a value is not provided. [[#2038](https://github.com/ansible/tower/issues/2038)]
* Add validation to prevent string "$encrypted$" from becoming a literal
  survey question default [[#518](https://github.com/ansible/awx/issues/518)].
* Enable the `--export` option for `ansible-inventory` via the environment
  variable [[#1253](https://github.com/ansible/awx/pull/1253)] so that
  group `variables` are imported to the group model.
* Prevent unwanted entries in activity stream due to `modified` time changes.
* API based deep copy feature via related `/api/v2/resources/N/copy/` endpoint
  [[#283](https://github.com/ansible/awx/issues/283)].
* Container Cluster-based dynamic scaling provisioning / deprovisioning instances,
  allow creating / modifying instance groups from the API, introduce instance
  group policies, consider both memory and CPU constraints, add the ability
  to disable nodes without removing them from the cluster
  [[#196](https://github.com/ansible/awx/issues/196)].
* Add additional organization roles [[#166](https://github.com/ansible/awx/issues/166)].
* Support fact caching for isolated instances [[#198](https://github.com/ansible/awx/issues/198)].
* Graphical UI for network inventory [[#611](https://github.com/ansible/awx/issues/611)].
* Restrict viewing and editing network UI canvas to users with inventory `admin_role`.
* Implement per-template, project, organization `custom_virtualenv`, a field that
  allows users to select one of multiple virtual environments set up on the filesystem
  [[#34](https://github.com/ansible/awx/issues/34)].
* Use events for running inventory updates, project updates, and other unified job
  types [[#200](https://github.com/ansible/awx/issues/200)].
* Prevent deletion of jobs when event processing is still ongoing.
* Prohibit job template callback when `inventory` is null
  [[#644](https://github.com/ansible/awx/issues/644)].
* Impose stricter criteria to admin users - organization admin role now
  necessary for all organizations target user is member of.
* Remove unused `admin_role` associated with users.
* Enforce max value for `SESSION_COOKIE_AGE`
  [[#1651](https://github.com/ansible/awx/issues/1651)].
* Add stricter validation to `order_by` query params
  [[#776](https://github.com/ansible/awx/issues/776)].
* Consistently log uncaught task exceptions [[#1257](https://github.com/ansible/awx/issues/1257)].
* Do not show value of variable of `with_items` iteration when `no_log` is set.
* Change external logger to lazily create handler from settings on every log
  emission, replacing server restart. Allows use in OpenShift deployments.
* Allow job templates using previously-synced git projects to run without network
  access to source control [[#287](https://github.com/ansible/awx/issues/287)].
* Automatically run a project update if sensitive fields change like `scm_url`.
* Disallow relaunching jobs with `execute_role` if another user provided prompts.
* Show all teams to organization admins if setting `ORG_ADMINS_CAN_SEE_ALL_USERS` is enabled.
* Allow creating schedules and workflow nodes from job templates that use
  credentials which prompt for passwords if `ask_credential_on_launch` is set.
* Set `execution_node` in task manager and submit `waiting` jobs to only the
  queue for the specific instance job is targeted to run on
  [[#1873](https://github.com/ansible/awx/issues/1873)].
* Switched authentication to Django sessions.
* Implemented OAuth2 support for token based authentication [[#21](https://github.com/ansible/awx/issues/21)].
* Added the ability to forcibly expire sessions through `awx-manage expire_sessions`.
* Disallowed using HTTP PUT/PATCH methods to modify existing jobs in Job Details API endpoint.
* Changed the name of the session length setting from `AUTH_TOKEN_EXPIRATION` to `SESSION_COOKIE_AGE`.
* Changed the name of the session length setting from `AUTH_TOKEN_PER_USER` to `SESSIONS_PER_USER`.

3.2.0
=====
* added a new API endpoint - `/api/v1/settings/logging/test/` - for testing
  external log aggregrator connectivity
  [[#5164](https://github.com/ansible/ansible-tower/issues/5164)]
* allow passing `-e create_preload_data=False` to skip creating default
  organization/project/inventory/credential/job_template during Tower
  installation
  [[#5746](https://github.com/ansible/ansible-tower/issues/5746)]
* removed links from group to `inventory_source` including the field and
  related links, removed `start` and `schedule` capabilities from
  group serializer and added `user_capabilities` to inventory source
  serializer, allow user creation and naming of inventory sources
  [[#5741](https://github.com/ansible/ansible-tower/issues/5741)]
* support sourcing inventory from a file inside of a project's source
  tree [[#2477](https://github.com/ansible/ansible-tower/issues/2477)]
* added support for custom cloud and network credential types, which give the
  customer the ability to modify environment variables, extra vars, and
  generate file-based credentials (such as file-based certificates or .ini
  files) at `ansible-playbook` runtime
  [[#5876](https://github.com/ansible/ansible-tower/issues/5876)]
* added support for assigning multiple cloud and network credential types on
  `JobTemplates`.  ``JobTemplates`` can prompt for "extra credentials" at
  launch time in the same manner as promptable machine credentials
  [[#5807](https://github.com/ansible/ansible-tower/issues/5807)]
  [[#2913](https://github.com/ansible/ansible-tower/issues/2913)]
* custom inventory sources can now specify a ``Credential``; you
  can store third-party credentials encrypted within Tower and use their
  values from within your custom inventory script (by - for example - reading
  an environment variable or a file's contents)
  [[#5879](https://github.com/ansible/ansible-tower/issues/5879)]
* Added support for configuring groups of instance nodes to run tower
  jobs [[#5898](https://github.com/ansible/ansible-tower/issues/5898)]
* Fixed an issue installing Tower on multiple nodes where cluster
  internal node references are used
  [[#6231](https://github.com/ansible/ansible-tower/pull/6231)]
* Tower now uses a modified version of [Fernet](https://github.com/fernet/spec/blob/master/Spec.md).
  Our `Fernet256` class uses `AES-256-CBC` instead of `AES-128-CBC` for all encrypted fields.
  [[#826](https://github.com/ansible/ansible-tower/issues/826)]
* Added the ability to set custom environment variables set for playbook runs,
  inventory updates, project updates, and notification sending.
  [[#3508](https://github.com/ansible/ansible-tower/issues/3508)]
* Added --diff mode to Job Templates and Ad-Hoc Commands.  The diff can be found in the
  standard out when diff mode is enabled.  [[#4525](https://github.com/ansible/ansible-tower/issues/4325)]
* Support accessing some Tower resources via their name-related unique identifiers apart from primary keys.
(named URL) [[#3362](https://github.com/ansible/ansible-tower/issues/3362)]
* Support TACACS+ authentication. [[#3400](https://github.com/ansible/ansible-tower/issues/3400)]
* Support sending system logs to external log aggregators via direct TCP/UDP connection.
[[#5783](https://github.com/ansible/ansible-tower/pull/5783)]
* Remove Rackspace as a supported inventory source type and credential type.
[[#6117](https://github.com/ansible/ansible-tower/pull/6117)]
* Changed names of tower-mange commands `register_instance` -> `provision_instance`,
  `deprovision_node` -> `deprovision_instance`, and `instance_group_remove` -> `remove_from_queue`,
  which backward compatibility support for 3.1 use pattern
  [[#6915](https://github.com/ansible/ansible-tower/issues/6915)]
