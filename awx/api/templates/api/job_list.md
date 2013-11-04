{% include "api/list_create_api_view.md" %}

If the `job_template` field is specified, any fields not explicitly provided
for the new job (except `name` and `description`) will use the default values
from the job template.
