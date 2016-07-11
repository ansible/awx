{% include "api/sub_list_create_api_view.md" %}

Labels not associated with any other resources are deleted. A label can become disassociated with a resource as a result of 3 events.

1. A label is explicitly diassociated with a related job template
2. A job is deleted with labels
3. A cleanup job deletes a job with labels

{% include "api/_new_in_awx.md" %}
