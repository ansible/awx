# Relaunch on Hosts with Status

This feature allows the user to relaunch a job, targeting only a subset
of hosts that had a particular status in the prior job.

### API Design of Relaunch

#### Basic Relaunch

POST to `/api/v2/jobs/N/relaunch/` without any request data should relaunch
the job with the same `limit` value that the original job used, which
may be an empty string.

#### Relaunch by Status

Providing request data containing `{"hosts": "<status>"}` should change
the `limit` of the relaunched job to target the hosts matching that status
from the previous job (unless the default option of "all" is used).
The options and meanings of `<status>` include:

 - all: relaunch without changing the job limit
 - ok: relaunch against all hosts with >=1 tasks that returned the "ok" status
 - changed: relaunch against all hosts with >=1 tasks had a changed status
 - failed: relaunch against all hosts with >=1 tasks failed plus all unreachable hosts
 - unreachable: relaunch against all hosts with >=1 task when they were unreachable

These correspond to the playbook summary states from a playbook run, with
the notable exception of "failed" hosts. Ansible does not count an unreachable
event as a failed task, so unreachable hosts can (and often do) have no
associated failed tasks. The "failed" status here will still target both
status types, because Ansible will mark the _host_ as failed and include it
in the retry file if it was unreachable.

### Relaunch Endpoint

Doing a GET to the relaunch endpoint should return additional information
regarding the host summary of the last job. Example response:

```json
{
    "passwords_needed_to_start": [],
    "retry_counts": {
        "all": 30,
        "failed": 18,
        "ok": 25,
        "changed": 4,
        "unreachable": 9
    }
}
```

If the user launches, providing a status for which there were 0 hosts,
then the request will be rejected.

# Acceptance Criteria

Scenario: user launches a job against host "foobar", and the run fails
against this host. User changes name of host to "foo", and relaunches job
against failed hosts. The `limit` of the relaunched job should reference
"foo" and not "foobar".

The user should be able to provide passwords on relaunch, while also
running against hosts of a particular status.

Not providing the "hosts" key in a POST to the relaunch endpoint should
relaunch the same way that relaunching has previously worked.

If a playbook provisions a host, this feature should behave reasonably
when relaunching against a status that includes these hosts.

Feature should work even if hosts have tricky characters in their names,
like commas.

Also need to consider case where a task `meta: clear_host_errors` is present
inside a playbook, and that the retry subset behavior is the same as Ansible
for this case.
