# List All {{ model_verbose_name_plural|title }} for {{ parent_model_verbose_name|title|anora }}:

Make a GET request to this resource to retrieve a list of all
{{ model_verbose_name_plural }} directly or indirectly belonging to this
{{ parent_model_verbose_name }}.

{% include "api/_list_common.md" %}
