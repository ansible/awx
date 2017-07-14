# Tower as an Ansible Fact Cache
Tower can store and retrieve per-host facts via an Ansible Fact Cache Plugin. This behavior is configurable on a per-job-template basis. When enabled, Tower will serve fact requests for all Hosts in an Inventory related to the Job running. This allows users to use Job Templates with `--limit` while still having access to the entire Inventory of Host facts. The Tower Ansible Fact Cache supports a global timeout settings that it enforces per-host. The setting is available in the CTiT interface under the Jobs category with the name `ANSIBLE_FACT_CACHE_TIMEOUT` and is in seconds.

## Tower Fact Cache Implementation Details
### Tower Injection
In order to understand the behavior of Tower as a fact cache you will need to understand how fact caching is achieved in Tower. Upon a Job invocation with `use_fact_cache=True`, Tower will inject, into memcached, all `ansible_facts` associated with each Host in the Inventory associated with the Job. Jobs invoked with `use_fact_cache=False` will not inject `ansible_facts` into memcached. The cache key is of the form `inventory_id-host_name` so that hosts with the same name in different inventories do not clash. A list of all hosts in the inventory is also injected into memcached with key `inventory_id` and value `[host_name1, host_name2, ..., host_name3]`.

### Ansible plugin usage
The Ansible fact cache plugin that ships with Tower will only be enabled on Jobs that have fact cache enabled, `use_fact_cache=True`. The fact cache plugin running in Ansible will connect to the same memcached instance. A `get()` call to the fact cache interface in Ansible will result in a looked into memcached for the host-specific set of facts. A `set()` call to the fact cache will result in an update to memcached record along with the modified time.

### Tower Cache to DB
When a Job finishes running that has `use_fact_cache=True` enabled, Tower will go through memcached and get all records for the hosts in the Inventory. Any records with update times newer than the database per-host `ansible_facts_modified` value will result in the `ansible_facts`, `ansible_facts_modified` from memcached being saved to the database. Note that the last value of the Ansible fact cache is retained in `ansible_facts`. The globla timeout and/or individual job template `use_fact_cache` setting will not clear the per-host `ansible_facts`.

### Caching Behavior
Tower will always inject the host `ansible_facts` into memcached. The Ansible Tower Fact Cache Plugin will choose to present the cached values to the user or not based on the per-host `ansible_facts_modified` time and the global `ANSIBLE_FACT_CACHE_TIMEOUT`.

## Tower Fact Logging
New and changed facts will be logged via Tower's logging facility. Specifically, to the `system_tracking` namespace or logger. The logging payload will include the fields: `host_name`, `inventory_id`, and `ansible_facts`. Where `ansible_facts` is a dictionary of all ansible facts for `host_name` in Tower Inventory `inventory_id`. 

## Integration Testing
* ensure `clear_facts` set's `hosts/<id>/ansible_facts` to `{}`
* ensure that `gather_facts: False` does NOT result in clearing existing facts
* ensure that the when a host fact timeout is reached, that the facts are not used from the cache
