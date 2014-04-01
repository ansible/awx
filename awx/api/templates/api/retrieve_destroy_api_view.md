# Retrieve {{ model_verbose_name|title }}:

Make GET request to this resource to retrieve a single {{ model_verbose_name }}
record containing the following fields:

{% include "api/_result_fields_common.md" %}

# Delete {{ model_verbose_name|title }}:

Make a DELETE request to this resource to delete this {{ model_verbose_name }}.

{% include "api/_new_in_awx.md" %}
