### Constructed inventory in AWX

Constructed inventory is a separate "kind" of inventory, along-side of
normal (manual) inventories and "smart" inventories.
The functionality overlaps with smart inventory, and it is intended that
smart inventory is sunsetted and will be eventually removed.

#### Demo Problem

This is branched from original demo at:

https://github.com/AlanCoding/Ansible-inventory-file-examples/tree/master/issues/AWX371

Consider that we have 2 original "source" inventories named "East" and "West".

```
# East inventory original contents
host1 account_alias=product_dev
host2 account_alias=product_dev state=shutdown
host3 account_alias=sustaining
```

```
# West inventory original contents
host4 account_alias=product_dev
host6 account_alias=product_dev state=shutdown
host5 account_alias=sustaining state=shutdown
```

The user's intent is to operate on _shutdown_ hosts in the _product_dev_ group.
So these are two AND conditions that we want to filter on.

To accomplish this, the user will create a constructed inventory with
the following properties.

`source_vars` =

```yaml
plugin: constructed
strict: true
use_vars_plugins: true  # https://github.com/ansible/ansible/issues/75365
groups:
  shutdown: resolved_state == "shutdown"
  shutdown_in_product_dev: resolved_state == "shutdown" and account_alias == "product_dev"
compose:
  resolved_state: state | default("running")
```

`limit` = "shutdown_in_product_dev"

Then when running a job template against the constructed inventory, it should
act on host2 and host6, because those are the two hosts that fit the criteria.

#### Mechanic

The constructed inventory contents will be materialized by an inventory update
which runs via `ansible-inventory`.
This is always configured to update-on-launch before a job,
but the user can still select a cache timeout value in case this takes too long.

When creating a constructed inventory, the API enforces that it always has 1
inventory source associated with it.
All inventory updates have an associated inventory source, and the fields
needed for constructed inventory (`source_vars` and `limit`) are fields
on the inventory source model normally.

#### Capabilities

In addition to filtering on hostvars, users will be able to filter based on
facts, which are prepared before the update in the same way as for jobs.

For filtering on related objects in the database, users will need to use "meta"
vars that are automatically prepared by the server.
These have names such as:
 - `awx_inventory_name`
 - `awx_inventory_id`

#### Best Practices

It is very important to set the `strict` parameter to `True` so that users
can debug problems with their templates, because these can get complicated.
If the template fails to render, users will get an error in the
associated inventory update for that constructed inventory.

When encountering errors, it may be prudent to increase `verbosity` to get
more details.
