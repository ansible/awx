## Launch-time Configurations / Prompting

Admins of templates in AWX have the option to allow fields to be over-written
by user-provided values at the time of launch. The job that runs will
then use the launch-time values in lieu of the template values.

Fields that can be prompted for, and corresponding "ask_" variables
(which exist on the template and must be set to `true` to enable prompting)
are the following.

##### Standard Pattern with Character Fields

 - `ask_<variable>_on_launch` allows use of
   - `<variable>`

The standard pattern applies to fields

 - `job_type`
 - `job_tags`
 - `skip_tags`
 - `limit`
 - `diff_mode`
 - `verbosity`

##### Non-Standard Cases (Credentials Changing in Tower 3.3)

 - `ask_variables_on_launch` allows unrestricted use of
   - `extra_vars`
 - Enabled survey allows restricted use of
   - `extra_vars`, only for variables in survey (with qualifiers)
 - `ask_credential_on_launch` allows use of
   - `credential`
   - `vault_credential` / `extra_credentials` / `credentials`
     (version-dependent, see notes below)
 - `ask_inventory_on_launch` allows use of
   - `inventory`

Surveys are a special-case of prompting for variables - applying a survey to
a template white-lists variable names in the survey spec (requires the survey
spec to exist and `survey_enabled` to be true). On the other hand,
if `ask_variables_on_launch` is true, users can provide any variables in
extra_vars.

Prompting enablement for several types of credentials is controlled by a single
field. On launch, multiple types of credentials can be provided in their respective fields
inside of `credential`, `vault_credential`, and `extra_credentials`. Providing
a credential that requirements password input from the user on launch is
allowed, and the password must be provided along-side the credential, of course.

If the job is being spawned using a saved launch configuration, however,
all non-machine credential types are managed by a many-to-many relationship
called `credentials` relative to the launch configuration object.
When the job is spawned, the credentials in that relationship will be
sorted into the job's many-to-many credential fields according to their
type (cloud vs. vault).

### Manual use of Prompts

Fields enabled as prompts in the template can be used for the following
actions in the API.

 - POST to `/api/v2/job_templates/N/launch/`
   - can accept all prompt-able fields
 - POST to `/api/v2/workflow_job_templates/N/launch/`
   - can only accept extra_vars
 - POST to `/api/v2/system_job_templates/N/launch/`
   - can accept certain fields, with no user configuration

### Saved Launch-time Configurations

Several other mechanisms which automatically launch jobs can apply prompts
at launch-time that are saved in advance.

 - Workflow nodes
 - Schedules
 - Job relaunch / re-scheduling

In the case of workflow nodes and schedules, the prompted fields are saved
directly on the model. Those models include Workflow Job Template Nodes,
Workflow Job Nodes (a copy of the first), and Schedules.

Jobs, themselves, have a configuration object stored in a related model,
but this is hidden from the API, and only used to prepare the correct
launch-time configuration for subsequent re-launch and re-scheduling of the job.

#### Workflow Node Launch Configuration (Changing in Tower 3.3)

Workflow job nodes have a special rule that `extra_vars` from their parent
workflow job will be combined with the variables that they provide in
`extra_data`, as well as artifacts from prior job runs. Both of these
sources of variables have higher precedence than the variables defined in
the node.

However, all the sources of variables that a workflow passes to a job it
spawns still abides by the rules of the template that the node uses. That
means that if the template has `ask_variables_on_launch` set to false with
no survey, neither the workflow JT or the artifacts will take effect
in the job that is spawned.

Behavior before the 3.3 release cycle was less-restrictive with passing
workflow variables to the jobs it spawned, allowing variables to take effect
even when the job template was not configured to allow it.

#### Job Relaunch and Re-scheduling

Job relaunch does not allow user to provide any new fields at the time of relaunch.
Relaunching will launch the job, re-applying all the prompts used at the
time of the original launch. This means that:

 - all prompts restrictions apply as-if the job was being launched with the
   current job template (even if it has been modified)
 - RBAC rules for prompted resources still apply

Those same rules apply when created a schedule from the
`/api/v2/schedule_job/` endpoint.

#### Credential Password Prompting Restrictions

If a job template uses a credential that is configured to prompt for a
password at launch, these passwords cannot be saved for later as part
of a save launch-time configuration. This is for security reasons.

Credential passwords _can_ be provided at time of relaunch.

### Validation

The general rule for validation:

> When a job is created from a template, only fields specifically configured
to be prompt-able are allowed to differ from the template to the job.

In other words, if no prompts (including surveys) are configured, a job
must be identical to the template it was created from, for all fields
that become `ansible-playbook` options.

#### Disallowed Fields (Changing in Tower 3.3)

If a manual launch provides fields not allowed by the rules of the template,
the behavior is:

 - Launches without those fields, ignores fields
   - lists fields in `ignored_fields` in POST response
 - With Tower 3.3, a 400 error is returned

#### Data Type Validation

All fields provided on launch, or saved in a launch-time configuration
for later, should be subject to the same validation that they would be
if saving to the job template model. For example, only certain values of
`job_type` are valid.

Surveys impose additional restrictions that violations of the survey
validation rules will prevent launch from proceeding.

#### Fields Required on Launch

Failing to provide required variables also results in a validation error.

#### Broken Saved Configurations

There are 2 types of invalid states:

 - cannot be launched
 - rejected prompts

If a job is spawned from schedule or a workflow in a state that has rejected
prompts, this should be logged, but the job should still be launched, without
those prompts applied.

If the job is spawned from a schedule or workflow in a state that cannot be
launched (typical example is a null `inventory`), then the job should be
created in an "error" state with `job_explanation` containing a summary
of what happened.
