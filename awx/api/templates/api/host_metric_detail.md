{% ifmeth GET %}
# Retrieve {{ model_verbose_name|title|anora }}:

Make GET request to this resource to retrieve a single {{ model_verbose_name }}
record containing the following fields:

{% include "api/_result_fields_common.md" %}
{% endifmeth %}

{% ifmeth DELETE %}
# Delete {{ model_verbose_name|title|anora }}:

Make a DELETE request to this resource to soft-delete this {{ model_verbose_name }}.

A soft deletion will mark the `deleted` field as true and exclude the host
metric from license calculations.
This may be undone later if the same hostname is automated again afterwards.
{% endifmeth %}
