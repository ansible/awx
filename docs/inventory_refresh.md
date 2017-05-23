# Inventory Refresh Overview
Tower should have an inventory view that is more aligned towards systems management
rather than merely maintaining inventory for automation.

## Inventory Source Promotion


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

### Smart Filter (host_filter)
The `SmartFilter` class handles our translation of the smart search string. We store the
filter value in the `host_filter` field for an inventory. This value should be expressed
the same way we express our existing smart searches.

    host_filter="search=foo"
    host_filter="groups__search=bar"
    host_filter="search=baz and groups_search=bang"
    host_filter="name=localhost or group__name=local"

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

### Background Deleition of Inventory

### InventorySource Hosts and Groups read-only
