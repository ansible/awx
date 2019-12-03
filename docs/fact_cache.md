# AWX as an Ansible Fact Cache

AWX can store and retrieve per-host facts via an Ansible Fact Cache Plugin.
This behavior is configurable on a per-job-template basis. When enabled, AWX
will serve fact requests for all Hosts in an Inventory related to the Job
running. This allows users to use Job Templates with `--limit` while still
having access to the entire Inventory of Host facts.

## AWX Fact Cache Implementation Details
### AWX Injection
In order to understand the behavior of AWX as a fact cache, you will need to
understand how fact caching is achieved in AWX. When a Job launches with
`use_fact_cache=True`, AWX will write all `ansible_facts` associated with
each Host in the associated Inventory as JSON files on the local file system
(one JSON file per host).  Jobs invoked with `use_fact_cache=False` will not
write `ansible_facts` files.

### Ansible Plugin Usage
When `use_fact_cache=True`, Ansible will be configured to use the `jsonfile`
cache plugin.  Any `get()` call to the fact cache interface in Ansible will
result in a JSON file lookup for the host-specific set of facts. Any `set()`
call to the fact cache will result in a JSON file being written to the local
file system.

### AWX Cache to DB
When a Job with `use_fact_cache=True` finishes running, AWX will look at all
of the local JSON files that represent the fact data.  Any records with file
modification times that have increased (because Ansible updated the file via
`cache.set()`) will result in the latest value being saved to the database.  On
subsequent playbook runs, AWX will _only_ inject cached facts that are _newer_
than `settings.ANSIBLE_FACT_CACHE_TIMEOUT` seconds.

## AWX Fact Logging
New and changed facts will be logged via AWX's logging facility, specifically
to the `system_tracking` namespace or logger. The logging payload will include
the fields `host_name`, `inventory_id`, and `ansible_facts`. Where
`ansible_facts` is a dictionary of all Ansible facts for `host_name` in AWX
Inventory `inventory_id`.

## Integration Testing
* Ensure `clear_facts` sets `hosts/<id>/ansible_facts` to `{}`.
* Ensure that `gather_facts: False` does NOT result in clearing existing facts.
* Ensure that when a host fact timeout is reached, that the facts are not used from the cache.
