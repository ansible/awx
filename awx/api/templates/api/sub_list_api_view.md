{% ifmeth GET %}
# List {{ model_verbose_name_plural|title }} for {{ parent_model_verbose_name|title|anora }}:

Make a GET request to this resource to retrieve a list of
{{ model_verbose_name_plural }} associated with the selected
{{ parent_model_verbose_name }}.

{% include "api/_list_common.md" %}
{% endifmeth %}
