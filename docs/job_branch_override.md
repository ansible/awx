## Job Branch Override

_Background:_ Projects specify the branch, tag, or reference to use from source control
in the `scm_branch` field.

This "Branch Override" feature allows project admins to delegate branch selection to
admins of Job Templates that use that project (requiring only project
`use_role`). Admins of Job Templates can further
delegate that ability to users executing the Job Template
(requiring only Job Template `execute_role`) by enabling
`ask_scm_branch_on_launch` on the Job Template.

### Source Tree Copy Behavior

_Background:_ Every job run has its own private data directory.
This folder is temporary, cleaned up at the end of the job run.

This directory contains a copy of the project source tree for the given
`scm_branch` while the job is running.

A new shallow copy is made for every job run.
Jobs are free to make changes to the project folder and make use of those
changes while it is still running.

#### Use Cases That No Long Work

With the introduction of this feature, the function of `scm_clean` is watered
down. It will still be possible to enable this function, and it will be
passed through as a parameter to the playbook as a tool for troubleshooting.
Two notable cases that lose support are documented below:

1) Setting `scm_clean` to `true` will no longer persist changes between job runs.

This means that jobs that rely on content which is not committed to source
control may fail now.

2) Because it is a shallow copy, this folder will not contain the full
git history for git project types.


### Project Revision Concerns

_Background:_
The revision of the default branch (specified as `scm_branch` of the project)
is stored when updated, and jobs using that project will employ this revision.

Providing a non-default `scm_branch` in a job comes with some restrictions,
which are unlike the normal update behavior.
If `scm_branch` is a branch identifier (not a commit hash or tag), then
the newest revision is pulled from the source control remote immediately
before the job starts.
This revision is shown in the `scm_revision` field of the
job and its respective project update.
This means that offline job runs are impossible for non-default branches.
To be sure that a job is running a static version from source control,
use tags or commit hashes.

Project updates do not save the revision of all branches, only the
project default branch.

The `scm_branch` field is not validated, so the project must update
to assure it is valid.
If `scm_branch` is provided or prompted for, the `playbook` field of
Job Templates will not be validated, and users will have to launch
the Job Template in order to verify presence of the expected playbook.


### Git Refspec

The field `scm_refspec` has been added to projects. This is provided by
the user or left blank.

A non-blank `scm_refspec` field will cause project updates (of any type)
to pass the `refspec` field when running the Ansible
git module inside of the `project_update.yml` playbook. When the git module
is provided with this field, it performs an extra `git fetch` command
to pull that refspec from the remote.

The refspec specifies what references the update will download from the remote.
Examples:

 - `refs/*:refs/remotes/origin/*`
    This will fetch all references, including even remotes of the remote
 - `refs/pull/*:refs/remotes/origin/pull/*`
    Github-specific, this will fetch all refs for all pull requests
 - `refs/pull/62/head:refs/remotes/origin/pull/62/head`
    This will fetch the ref for that one github pull request

For large projects, users should consider performance when
using the first or second examples here.

This parameter affects availability of the project branch, and can allow
access to references not otherwise available. For example, the third example
will allow the user to supply `pull/62/head` for `scm_branch`, which would
not be possible without the refspec field.

The Ansible git module always fetches `refs/heads/*`. It will do this
whether or not a custom refspec is provided. This means that a project's
branches and tags (and commit hashes therein) can be used as `scm_branch`
no matter what is used for `scm_refspec`.

The `scm_refspec` will affect which `scm_branch` fields can be used as overrides.
For example, you could set up a project that allows branch override with the
first or second refspec example, then use this in a Job Template
that prompts for `scm_branch`, then a client could launch the Job Template when
a new pull request is created, providing the branch `pull/N/head`,
then the Job Template would run against the provided GitHub pull request reference.
