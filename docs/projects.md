### Distributed project update concepts

Project updates serve an important role in maintaining the audit trail
of what actions were performed by an AWX server. They also serve the role
of assuring that the project folder contains the expected content on the local
file system before running a job in clustered AWX installations.

These two responsibilities are separated in the technical design of
project updates. The `job_type` field of a project update indicates which
function that update served.

 - a `job_type` of `check` (denoting Ansible "check mode") updates the
   last-known revision of the project saved in the database, but does not
   make persistent changes to the local file system on the instance it runs.
   This revision is surfaced in the field `scm_revision` in the project API.
 - a `job_type` of `run` updates the content of the project folder to the
   `scm_revision` of the project.

A run-type project update is performed on the same instance in the cluster
before running a job template in order to obtain the right playbook and
associated files. This type of update is denoted by a `launch_type` of `sync`.

Check-type project updates, on the other hand, can be ran from any instance
in the cluster. If a project is set to update on launch, this results in
_both_ a check-type project update and then a run-type project update before
the job template runs.

#### Delayed initial update for direct API clients

By default, the action of creating a project will launch a check type project
update, so that an initial value of `scm_revision` can be filled in.

There is a feature to skip this update, designed specifically for API clients
that wish to avoid bottlenecks.

 - provide field `skip_update=true` on project creation
 - on creation of subsequent job templates, validation of the `playbook` field
   is bypassed, so the client does not need to wait for project update
   completion before proceeding with the rest of its work
 - whenever a job template using the project runs, the revision discovered
   by the `run` type update will subsequently be used as the
   `scm_revision` of the project

This allows the client to reliably create resources sufficient to launch a job
without doing any polling.
