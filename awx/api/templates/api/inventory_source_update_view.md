# Update Inventory Source

Make a GET request to this resource to determine if the group can be updated
from its inventory source.  The response will include the following field:

* `can_update`: Flag indicating if this inventory source can be updated
  (boolean, read-only)

Make a POST request to this resource to update the inventory source.  If
successful, the response status code will be 202.  If the inventory source is
not defined or cannot be updated, a 405 status code will be returned.
