# Cancel Project Update

Make a GET request to this resource to determine if the project update can be
cancelled.  The response will include the following field:

* `can_cancel`: Indicates whether this update can be canceled (boolean,
  read-only)

Make a POST request to this resource to cancel a pending or running project
update.  The response status code will be 202 if successful, or 405 if the
update cannot be canceled.

{% include "main/_new_in_awx.md" %}
