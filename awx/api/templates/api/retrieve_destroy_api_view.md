{% ifmeth GET %}
# Retrieve {{ model_verbose_name|title|anora }}:

Make GET request to this resource to retrieve a single {{ model_verbose_name }}
record containing the following fields:

{% include "api/_result_fields_common.md" %}
{% endifmeth %}

{% ifmeth DELETE %}
# Delete {{ model_verbose_name|title|anora }}:

Make a DELETE request to this resource to delete this {{ model_verbose_name }}.
{% endifmeth %}
