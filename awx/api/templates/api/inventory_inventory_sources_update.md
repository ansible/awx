# Update Inventory Sources

Make a GET request to this resource to determine if any of the inventory sources for
this inventory can be updated. The response will include the following fields for each
inventory source:

* `inventory_source`: ID of the inventory_source
  (integer, read-only)
* `can_update`: Flag indicating if this inventory source can be updated
  (boolean, read-only)

Make a POST request to this resource to update the inventory sources. The response
status code will be a 202. The response will contain the follow fields for each of the individual
inventory sources:

* `status`: `started` or message why the update could not be started.
  (string, read-only)
* `inventory_update`: ID of the inventory update job that was started.
  (integer, read-only)
* `project_update`: ID of the project update job that was started if this inventory source is an SCM source.
  (interger, read-only, optional)

{% include "api/_new_in_awx.md" %}
