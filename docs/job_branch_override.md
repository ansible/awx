## Job Branch Specification

Background: Projects specify the branch to use from source control
in the `scm_branch` field.

This feature allows project admins to delegate branch selection to
admins of job templates that use that project (requiring only project
`use_role`). Admins of job templates can further
delegate that ability to users executing the job template
(requiring only job template `execute_role`) by enabling
`ask_scm_branch_on_launch` on the job template.

### Source Tree Copy Behavior

Every job run has its own private data directory. This folder is temporary,
cleaned up at the end of the job run.

This directory contains a copy of the project source tree for the given
branch the job is running.

A new copy is made for every job run.

This folder will not contain the full git history for git project types.

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
    This will fetch only the ref for that one github pull request

For large projects, users should consider performance when
using the first or second examples here. For example, if a github project
has over 40,000 pull requests, that refspec will fetch them all
during a project update.

This parameter affects availability of the project branch, and can allow
access to references not otherwise available. For example, the third example
will allow the user to use the branch `refs/pull/62/head`, which would
not be possible without the refspec field.

The Ansible git module always fetches `refs/heads/*`. It will do this
whether or not a custom refspec is provided. This means that a project's
branches and tags (and commit hashes therein) can be used as `scm_branch`
no matter what is used for `scm_refspec`.

The `scm_refspec` will affect which `scm_branch` fields can be used as overrides.
For example, you could set up a project that allows branch override with a refspec
of `refs/pull/*:refs/remotes/origin/pull/*`, then use this in a job template
that prompts for `scm_branch`, then a client could launch the job template when
a new pull request is created, providing the branch `refs/pull/N/head`,
then the job template would run against the provided github pull request reference.
