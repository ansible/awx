{% ifmeth GET %}
# Retrieve {{ model_verbose_name|title|anora }}:

Make GET request to this resource to retrieve a single {{ model_verbose_name }}
record containing the following fields:

{% include "api/_result_fields_common.md" %}
{% endifmeth %}

{% ifmeth PUT PATCH %}
# Update {{ model_verbose_name|title|anora }}:

Make a PUT or PATCH request to this resource to update this
{{ model_verbose_name }}.  The following fields may be modified:

{% with write_only=1 %}
{% include "api/_result_fields_common.md" with serializer_fields=serializer_update_fields %}
{% endwith %}
{% endifmeth %}

{% ifmeth PUT %}
For a PUT request, include **all** fields in the request.
{% endifmeth %}

{% ifmeth PATCH %}
For a PATCH request, include only the fields that are being modified.
{% endifmeth %}

{% ifmeth DELETE %}
# Delete {{ model_verbose_name|title|anora }}:

Make a DELETE request to this resource to delete this {{ model_verbose_name }}.
{% endifmeth %}
