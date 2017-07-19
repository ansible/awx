{% if has_named_url %}
### Note: starting from api v2, this resource object can be accessed via its named URL.
{% endif %}

# Retrieve {{ model_verbose_name|title }}:

Make GET request to this resource to retrieve a single {{ model_verbose_name }}
record containing the following fields:

{% include "api/_result_fields_common.md" %}

# Update {{ model_verbose_name|title }}:

Make a PUT or PATCH request to this resource to update this
{{ model_verbose_name }}.  The following fields may be modified:

{% with write_only=1 %}
{% include "api/_result_fields_common.md" with serializer_fields=serializer_update_fields %}
{% endwith %}

For a PUT request, include **all** fields in the request.

For a PATCH request, include only the fields that are being modified.

# Delete {{ model_verbose_name|title }}:

Make a DELETE request to this resource to delete this {{ model_verbose_name }}.

{% include "api/_new_in_awx.md" %}
