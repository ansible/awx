# Update Project

Make a GET request to this resource to determine if the project can be updated
from its SCM source and whether any passwords are required for the update.  The
response will include the following fields:

* `can_update`: Flag indicating if this project can be updated (boolean,
  read-only)
* `passwords_needed_to_update`: Password names required to update the project
  (array, read-only)

Make a POST request to this resource to update the project.  If any passwords
are required, they must be passed via POST data.

If successful, the response status code will be 202.  If any required passwords
are not provided, a 400 status code will be returned.  If the project cannot be
updated, a 405 status code will be returned.

{% include "api/_new_in_awx.md" %}
