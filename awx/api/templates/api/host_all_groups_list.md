# List All {{ model_verbose_name_plural|title }} for {{ parent_model_verbose_name|title|anora }}:

Make a GET request to this resource to retrieve a list of all
{{ model_verbose_name_plural }} of which the selected
{{ parent_model_verbose_name }} is directly or indirectly a member.

{% include "api/_list_common.md" %}
