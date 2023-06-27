## Launch-time Configurations / Prompting

Admins of templates in AWX have the option to allow fields to be overwritten
by user-provided values at the time of launch. The job that runs will
then use the launch-time values in lieu of the template values.

Fields that can be prompted for, and corresponding `"ask_"` variables
(which exist on the template and must be set to `true` to enable prompting)
are the following:


##### Standard Pattern With Character Fields

 - `ask_<variable>_on_launch` allows use of `<variable>`

The standard pattern applies to the following fields:

 - `job_type`
 - `skip_tags`
 - `limit`
 - `diff_mode`
 - `verbosity`
 - `scm_branch`


##### Non-Standard Cases

 - `ask_variables_on_launch` allows unrestricted use of `extra_vars`
 - `ask_tags_on_launch` allows use of `job_tags`
 - Enabled survey allows restricted use of `extra_vars`, only for variables in survey (with qualifiers)
 - `ask_credential_on_launch` allows use of `credentials`
 - `ask_inventory_on_launch` allows use of `inventory`

Surveys are a special-case of prompting for variables - applying a survey to
a template allows variable names in the survey spec (requires the survey
spec to exist and `survey_enabled` to be true). On the other hand,
if `ask_variables_on_launch` is true, users can provide any variables in
`extra_vars`.

Prompting enablement for all types of credentials is controlled by `ask_credential_on_launch`.
Clients can manually provide a list of credentials of any type, but only one of _each_ type, in
`credentials` on a POST to the launch endpoint.
If the job is being spawned by a saved launch configuration (such as a schedule),
credentials are managed by the many-to-many relationship `credentials` relative
to the launch configuration object.
The credentials in this relationship will either add to the job template's
credential list, or replace a credential in the job template's list if it
is the same type.


### Manual Use of Prompts

Fields enabled as prompts in the template can be used for the following
actions in the API:

 - POST to `/api/v2/job_templates/N/launch/` (can accept all prompt-able fields)
 - POST to `/api/v2/workflow_job_templates/N/launch/` (can accept certain fields, see `workflow.md`)
 - POST to `/api/v2/system_job_templates/N/launch/` (can accept certain fields, with no user configuration)

When launching manually, certain restrictions apply to the use of credentials:
 - If providing deprecated `extra_credentials`, this becomes the "legacy" method
   and imposes additional restrictions on relaunch,
   and is mutually exclusive with the use of `credentials` field
 - If providing `credentials`, existing credentials on the job template may
   only be removed if replaced by another credential of the same type
   this is so that relaunch will use the up-to-date credential on the template
   if it has been edited since the prior launch


#### Data Rules for Prompts

For the POST action to launch, data for "prompts" are provided as top-level
keys in the request data. There is a special-case to allow a list to be
provided for `credentials`, which is otherwise not possible in AWX API design.
The list of credentials provided in the POST data will become the list
for the spawned job.

Values of `null` are not allowed; if the field is not being over-ridden,
the key should not be given in the payload. A `400` should be returned if
this is done.

Example:

POST to `/api/v2/job_templates/N/launch/` with data:

```json
{
  "job_type": "check",
  "limit": "",
  "credentials": [1, 2, 4, 5],
  "extra_vars": {}
}
```

...where the job template has credentials `[2, 3, 5]`, and the credential type
are the following:

 - 1 - gce
 - 2 - ssh
 - 3 - gce
 - 4 - aws
 - 5 - openstack

Assuming that the job template is configured to prompt for all of these
fields, here is what happens in this action:

 - `job_type` of the job takes the value of "check"
 - `limit` of the job takes the value of `""`, which means that Ansible will
   target all hosts in the inventory, even though the job template may have
   been targeted to a smaller subset of hosts
 - The job uses the `credentials` with primary keys 1, 2, 4, and 5
 - `extra_vars` of the job template will be used without any overrides

If `extra_vars` in the request data contains some keys, these will
be combined with the job template `extra_vars` dictionary, with the
request data taking precedence.

Provided credentials will replace any job template credentials of the same
exclusive type. In the example, the job template
Credential 3 was replaced with the provided Credential 1, because a job
may only use one GCE credential because these two credentials define the
same environment variables and configuration file.
If the job had not provided the Credential 1, a 400 error would have been
returned because the job must contain the same types of credentials as its
job template.


### Saved Launch-time Configurations

Several other mechanisms which automatically launch jobs can apply prompts
at launch-time that are saved in advance:

 - Workflow nodes
 - Schedules
 - Job relaunch / re-scheduling
 - (partially) Workflow job templates

In the case of workflow nodes and schedules, the prompted fields are saved
directly on the model. Those models include Workflow Job Template Nodes,
Workflow Job Nodes (a copy of the first), and Schedules.

The many-to-many `credentials` field differs from other fields because
they are managed through a sub-endpoint relative to the node or schedule.
This relationship contains the _additional_ credentials to apply when
it spawns a job.

Jobs, themselves, have a configuration object stored in a related model,
and only used to prepare the correct launch-time configuration for subsequent
re-launch and re-scheduling of the job. To see these prompts for a particular
job, do a GET to `/api/v2/jobs/N/create_schedule/`.


#### Workflow Node Launch Configuration

Workflow job nodes will combine `extra_vars` from their parent
workflow job with the variables that they provide in
`extra_data`, as well as artifacts from prior job runs. Both of these
sources of variables have higher precedence than the variables defined in
the node.

All prompts that a workflow node passes to a spawned job abides by the
rules of the related template.
That means that if the node's job template has `ask_variables_on_launch` set
to false with no survey, the workflow node's variables will not
take effect in the job that is spawned.
If the node's job template has `ask_inventory_on_launch` set to false and
the node provides an inventory, this resource will not be used in the spawned
job. If a user creates a node that would do this, a 400 response will be returned.


#### Workflow Job Template Prompts

Workflow job templates are different from other cases because they do not have a
template directly linked, so their prompts are a form of action-at-a-distance.
When the node's prompts are gathered to spawn its job, any prompts from the workflow job
will take precedence over the node's value.

As a special exception, `extra_vars` from a workflow will not obey the job template survey
and prompting rules, both for historical and ease-of-understanding reasons.
This behavior may change in the future.

Other than that exception, job template prompting rules are still adhered to when
a job is spawned.


#### Job Relaunch and Re-scheduling

Job relaunch does not allow a user to provide any prompted fields at the time of relaunch.
Relaunching will re-apply all the prompts used at the
time of the original launch. This means that:

 - All prompts restrictions apply as if the job was being launched with the
   current job template (even if it has been modified)
 - RBAC rules for prompted resources still apply

Those same rules apply when creating a schedule from the
`/api/v2/schedule_job/` endpoint.

Jobs orphaned by a deleted job template can be relaunched,
but only with Organization or System Administrator privileges.


#### Credential Password Prompting Restriction

If a job template uses a credential that is configured to prompt for a
password at launch, these passwords cannot be saved for later as part
of a saved launch-time configuration. This is for security reasons.

Credential passwords _can_ be provided at time of relaunch.


### Validation

The general rule for validation:

> When a job is created from a template, only fields specifically configured
to be prompt-able are allowed to differ from the template to the job.

In other words, if no prompts (including surveys) are configured, a job
must be identical to the template it was created from, for all fields
that become `ansible-playbook` options.


#### Disallowed Fields

If a manual launch provides fields not allowed by the rules of the template,
the behavior is:

 - Launches without those fields, ignores fields
 - lists fields in `ignored_fields` in POST response


#### Data Type Validation

All fields provided on launch, or saved in a launch-time configuration
for later, should be subject to the same validation that they would be
if saving to the job template model. For example, only certain values of
`job_type` are valid.

Surveys impose additional restrictions, and violations of the survey
validation rules will prevent launch from proceeding.


#### Fields Required on Launch

Failing to provide required variables also results in a validation error
when manually launching. It will also result in a 400 error if the user
fails to provide those fields when saving a workflow job template node or schedule.


#### Broken Saved Configurations

If a job is spawned from schedule or a workflow in a state that has rejected
prompts, this should be logged, but the job should still be launched, without
those prompts applied.

If the job is spawned from a schedule or workflow in a state that cannot be
launched (typical example is a null `inventory`), then the job should be
created in an "error" state with `job_explanation` containing a summary
of what happened.


### Scenarios to Cover

**Variable Precedence**
  - Schedule has survey answers for workflow job template survey
  - Workflow job template has node that has answers to job template survey
  - On launch, the schedule answers override all others

**Survey Password Durability**
   - Schedule has survey password answers from workflow job template survey
   - Workflow job template node has answers to different password questions from job template survey
   - Saving with `"$encrypted$"` value will either:
     - become a no-op, removing the key if a valid question default exists
     - replace with the database value if question was previously answered
   - Final job it spawns has both answers encrypted

**POST to Associate Credential to Workflow Job Template Node**
   - Requires admin to WFJT and execute to job template
   - This is in addition to the restriction of `ask_credential_on_launch`

**Credentials Merge Behavior**
   - Job template has machine & cloud credentials, set to prompt for credential on launch
   - Schedule for job template provides no credentials
   - Spawned job still uses all job template credentials
