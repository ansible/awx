# Update Project

Make a GET request to this resource to determine if the project can be updated
from its SCM source.  The response will include the following field:

* `can_update`: Flag indicating if this project can be updated (boolean,
  read-only)

Make a POST request to this resource to update the project.  If the project
cannot be updated, a 405 status code will be returned.
