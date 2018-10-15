Generate inventory group and host data as needed for an inventory script.

Refer to [Dynamic Inventory](http://docs.ansible.com/intro_dynamic_inventory.html)
for more information on inventory scripts.

## List Response

Make a GET request to this resource without query parameters to retrieve a JSON
object containing groups, including the hosts, children and variables for each
group.  The response data is equivalent to that returned by passing the
`--list` argument to an inventory script.

Specify a query string of `?hostvars=1` to retrieve the JSON
object above including all host variables.  The `['_meta']['hostvars']` object
in the response contains an entry for each host with its variables.  This
response format can be used with Ansible 1.3 and later to avoid making a
separate API request for each host.  Refer to
[Tuning the External Inventory Script](http://docs.ansible.com/developing_inventory.html#tuning-the-external-inventory-script)
for more information on this feature.

By default, the inventory script will only return hosts that
are enabled in the inventory.  This feature allows disabled hosts to be skipped
when running jobs without removing them from the inventory.  Specify a query
string of `?all=1` to return all hosts, including disabled ones.

Specify a query string of `?towervars=1` to add variables
to the hostvars of each host that specifies its enabled state and database ID.

Specify a query string of `?subset=slice2of5` to produce an inventory that
has a restricted number of hosts according to the rules of job slicing.

To apply multiple query strings, join them with the `&` character, like `?hostvars=1&all=1`.

## Host Response

Make a GET request to this resource with a query string similar to
`?host=HOSTNAME` to retrieve a JSON object containing host variables for the
specified host.  The response data is equivalent to that returned by passing
the `--host HOSTNAME` argument to an inventory script.
