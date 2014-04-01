# Retrieve {{ model_verbose_name|title }}:

Make GET request to this resource to retrieve a single {{ model_verbose_name }}
record containing the following fields:

{% include "api/_result_fields_common.md" %}

# Update {{ model_verbose_name|title }}:

Make a PUT or PATCH request to this resource to update this
{{ model_verbose_name }}.  The following fields may be modified:

{% with write_only=1 %}
{% include "api/_result_fields_common.md" %}
{% endwith %}

For a PUT request, include **all** fields in the request.

For a PATCH request, include only the fields that are being modified.

{% include "api/_new_in_awx.md" %}
