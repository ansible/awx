# Execution Environments

All jobs use container isolation for environment consistency and security.
Compliant images are referred to as Execution Environments (EE)s.
For more information, see [ansible-runner EE docs](https://ansible-runner.readthedocs.io/en/latest/execution_environments.html)
for information on how container isolation works, and see [ansible-builder docs](https://ansible-builder.readthedocs.io/en/latest/index.html)
for instructions on how to build them.

The Execution Environment model has an `image` field for the image identifier which will be used by jobs.
The job details view will link to the execution environment that the job uses.

## Creating and using EEs

Users with and organization's `execution_environment_admin_role` can create new EEs in that organization.
The RBAC rules follow standard rules for org-scoped resources.

Only superusers can create global EEs (null organization).
These can become the global job default in certain circumstances.

### Pre-created EEs

Installers should run the `awx-manage register_default_execution_environments` command to pre-populate
the system with some EEs defined in settings. This will create:

 - a control plane EE - corresponding to the `CONTROL_PLANE_EXECUTION_ENVIRONMENT` setting
 - global job EEs - all images enumerated in the `GLOBAL_JOB_EXECUTION_ENVIRONMENTS` setting

These EEs are critical for system function, so this command must be ran for AWX to be functional.
All EEs created by this command are global (do not belong to an organization).

### Project Update EE Precedence

Project updates will always use the control plane execution environment.

### Job, Ad Hoc Commands, and inventory update EE Precedence

Jobs will use the first available execution environment in this list:

1. an EE from the template the spawned the job
2. the `default_environment` defined on the project that the job uses
3. the `default_environment` defined on the organization of the job (a direct API field)
4. the `default_environment` defined on the organization of the inventory the job uses
5. the global job default EE

This global default job default EE will be the first available out of:

1. the `DEFAULT_EXECUTION_ENVIRONMENT` setting
2. Any images from the `GLOBAL_JOB_EXECUTION_ENVIRONMENTS` setting
3. Any other global EEs (null organization)

If more than 1 EE fits these criteria, then the most recently created one will be used.

## Migrating from Custom Virtual Environments

If you have installed dependencies inside of custom virtual environments in
a prior release, then have a look at this series of commands for help migrating
dependencies out of the venvs and into EEs.

 - `awx-manage list_custom_venvs`
 - `awx-manage custom_venv_associations`
 - `awx-manage export_custom_venv`
