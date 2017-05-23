# Inventory Refresh Overview
Tower should have an inventory view that is more aligned towards systems management
rather than merely maintaining inventory for automation.

## Inventory Source Promotion
Starting with Tower 3.2, `InventorySource` will be associated directly with an `Inventory`.


## Fact Searching and Caching


## Smart Inventory
Starting in Tower 3.2, Tower will support the ability to define a _Smart Inventory_.
You will define the inventories using the same language we currently support
in our _Smart Search_.

### Inventory Changes
* The `Inventory` model has a new field called `kind`. The default of this field will be blank
for normal inventories and set to `smart` for smart inventories.

* `Inventory` model as a new field called `host_filter`. The default of this field will be blank
for normal inventories. When `host_filter` is set AND the inventory `kind` is set to `smart`
is the combination that makes a _Smart Inventory_.

### Smart Filter (host__filter)
The `SmartFilter` class handles our translation of the smart search string. We store the
filter value in the `host_filter` field for an inventory. This value should be expressed
the same way we express our existing smart searches.

    host_filter="search=foo"
    host_filter="group__search=bar"
    host_filter="search=baz and group__search=bang"
    host_filter="name=localhost or group__name=local"

Creating a new _Smart Inventory_ for all of our GCE and EC2 groups might look like this:

    HTTP POST /api/v2/inventories/

    {
        "name": "GCE and EC2 Smart Inventory",
        "kind": "smart",
        "host_filter": "group__search=ec2 and group__search=gce"
        ...
    }

### Acceptance Critera
When verifying acceptance we should ensure the following statements are true:

* `Inventory` has a new field named `kind` that defaults to empty and
can only be set to `smart`.
* `Inventory` has a new field named `host_filter` to empty and can only be
set to a valid _SmartFilter_ string.
* `Inventory` with a `host_filter` set and a `kind` of `smart` will have
a `hosts` list reflecting the results of searching `/hosts` with the same
smart search that is set in the `host_filter`.

### API Concerns
There are no breaking or backwards incompatible changes for this feature.


## Other Changes

### Inventory update all inventory__sources
A new endpoint `/api/v2/inventories/:id/update_inventory_sources` has been added. This endpoint
functions in the same way that `/api/v2/inventory_source/:id/update` functions for a single
`InventorySource` with the exception that it updates all of the inventory sources for the
`Inventory`.

`HTTP GET /api/v2/inventories/:id/update_inventory_sources` will list all of the inventory
sources and if they will be updated when a POST to the same endpoint is made. The result of
this request will look like this:

    {
        [
            {"inventory_source": 1, "can_update": True},
            {"inventory_source": 2, "can_update": False},
        ]
    }

When making a POST to the same endpoint, the response will contain a status as well as the job ID for the update.

    POST /api/v2/inventories/:id/update_inventory_sources

    {
        [
            {"inventory_update": 20, "inventory_source": 1, "status": "started"},
            {"inventory_update": 21, "inventory_source": 2, "status": "Could not start because `can_update` returned False"}
        ]
    }


### Background deleition of Inventory

### InventorySource Hosts and Groups read-only
