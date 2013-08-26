{% include "main/retrieve_api_view.md" %}

# Update {{ model_verbose_name|title }}:

Make a PUT or PATCH request to this resource to update this
{{ model_verbose_name }}.  The following fields may be modified:

{% with write_only=1 %}
{% include "main/_result_fields_common.md" %}
{% endwith %}

For a PUT request, include **all** fields in the request.

For a PATCH request, include only the fields that are being modified.

# Delete {{ model_verbose_name|title }}:

Make a DELETE request to this resource to delete this {{ model_verbose_name }}.

{% if new_in_13 %}> _New in AWX 1.3_{% endif %}
