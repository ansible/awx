# List {{ model_verbose_name_plural|title }} for this {{ parent_model_verbose_name|title }}:

Make a GET request to this resource to retrieve a list of
{{ model_verbose_name_plural }} associated with the selected
{{ parent_model_verbose_name }}.

{% include "api/_list_common.md" %}

{% include "api/_new_in_awx.md" %}
