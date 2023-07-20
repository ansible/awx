# Execution Environments

All jobs use container isolation for environment consistency and security.
Compliant images are referred to as Execution Environments (EE)s.

For more information about the EE technology as well as how to build and test EEs, see:
- [Getting started with Execution Environments guide](https://docs.ansible.com/ansible/devel/getting_started_ee/index.html)
- [Ansible Builder documentation](https://ansible.readthedocs.io/projects/builder/en/latest/)

The Execution Environment model has an `image` field for the image identifier which will be used by jobs.
The job details view will link to the execution environment that the job uses.

## Creating and using EEs

Users with an organization's `execution_environment_admin_role` can create new EEs in that organization.
The RBAC rules follow standard rules for org-scoped resources.

EEs without an organization (value is null in the API) are global EEs.
Only superusers can create global EEs.
These can become the global job default in certain circumstances.

### Pre-created EEs

Installers should run the `awx-manage register_default_execution_environments` command to pre-populate
the system with some EEs defined in settings. This will create:

 - the control plane EE - corresponding to the `CONTROL_PLANE_EXECUTION_ENVIRONMENT` setting
 - global job EEs - all images enumerated in the `GLOBAL_JOB_EXECUTION_ENVIRONMENTS` setting

These EEs are critical for system function, so this command must be ran for AWX to be functional.
All EEs created by this command are global EEs.

### Project Update EE Precedence

Project updates will always use the control plane EE.

### Job, Ad Hoc Commands, and inventory update EE Precedence

Jobs will use the first available execution environment in this list:

1. the `execution_environment` defined on the template (job template or inventory source) that spawned the job
2. the `default_environment` defined on the project that the job uses
3. the `default_environment` defined on the organization of the job
4. the `default_environment` defined on the organization of the inventory the job uses
5. the current `DEFAULT_EXECUTION_ENVIRONMENT` setting (configurable at `/api/v2/settings/jobs/`)
6. Any image from the `GLOBAL_JOB_EXECUTION_ENVIRONMENTS` setting
7. Any other global EE

If more than one EE fits a criteria (applies for 6 and 7), then the most recently created one will be used.

## Migrating from Custom Virtual Environments

If you have installed dependencies inside of custom virtual environments in
a prior release, then have a look at this series of commands for help migrating
dependencies out of the venvs and into EEs.

 - `awx-manage list_custom_venvs`
 - `awx-manage custom_venv_associations`
 - `awx-manage export_custom_venv`

Follow those in order, and read the help text to see what arguments are necessary.

Output from the `awx-manage export_custom_venv -q ..` command can
be a starting point for writing an `ansible-builder` definition file.
