# Relaunch on Hosts with Status

This feature allows the user to relaunch a job, targeting only the hosts marked
as "failed" in the original job.

### Definition of "failed"

This feature will relaunch against "failed hosts" in the original job, which
is different from "hosts with failed tasks". Unreachable hosts can have
no failed tasks. This means that the count of "failed hosts" can be different
from the failed count, given in the summary at the end of a playbook.

This definition corresponds to Ansible `.retry` files.

### API Design of Relaunch

#### Basic Relaunch

POSTs to `/api/v2/jobs/N/relaunch/` without any request data should relaunch
the job with the same `limit` value that the original job used, which
may be an empty string.

This is implicitly the "all" option, mentioned below.

#### Relaunch by Status

Providing request data containing `{"hosts": "failed"}` should change
the `limit` of the relaunched job to target failed hosts from the previous
job. Hosts will be provided as a comma-separated list in the limit. Formally,
these are options:

 - all: relaunch without changing the job limit
 - failed: relaunch against all hosts

### Relaunch Endpoint

Doing a GET to the relaunch endpoint should return additional information
regarding the host summary of the last job. Example response:

```json
{
    "passwords_needed_to_start": [],
    "retry_counts": {
        "all": 30,
        "failed": 18
    }
}
```

If the user launches, providing a status for which there were 0 hosts,
then the request will be rejected. For example, if a GET yielded:

```json
{
    "passwords_needed_to_start": [],
    "retry_counts": {
        "all": 30,
        "failed": 0
    }
}
```

...then a POST of `{"hosts": "failed"}` should return a descriptive response
with a 400-level status code.

# Acceptance Criteria

Scenario: User launches a job against host "foobar", and the run fails
against this host. User changes name of host to "foo", and relaunches job
against failed hosts. The `limit` of the relaunched job should reference
"foo" and not "foobar".

The user should be able to provide passwords on relaunch, while also
running against hosts of a particular status.

Not providing the "hosts" key in a POST to the relaunch endpoint should
relaunch the same way that relaunching has previously worked.

If a playbook provisions a host, this feature should behave reasonably
when relaunching against a status that includes these hosts.

This feature should work even if hosts have tricky characters in their names,
like commas.

One may also need to consider cases where a task `meta: clear_host_errors` is present
inside a playbook; the retry subset behavior is the same as Ansible's
for this case.
