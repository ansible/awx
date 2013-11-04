# Update Inventory Source

Make a GET request to this resource to determine if the group can be updated
from its inventory source and whether any passwords are required for the
update.  The response will include the following fields:

* `can_start`: Flag indicating if this job can be started (boolean, read-only)
* `passwords_needed_to_update`: Password names required to update from the
  inventory source (array, read-only)

Make a POST request to this resource to update the inventory source.  If any
passwords are required, they must be passed via POST data.

If successful, the response status code will be 202.  If any required passwords
are not provided, a 400 status code will be returned.  If the inventory source
is not defined or cannot be updated, a 405 status code will be returned.

{% include "api/_new_in_awx.md" %}
