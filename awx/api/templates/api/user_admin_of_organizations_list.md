# List {{ model_verbose_name_plural|title }} Administered by this {{ parent_model_verbose_name|title }}:

Make a GET request to this resource to retrieve a list of
{{ model_verbose_name_plural }} of which the selected
{{ parent_model_verbose_name }} is an admin.

{% include "api/_list_common.md" %}
