# List {{ model_verbose_name_plural|title }}:

Make a GET request to this resource to retrieve the list of
{{ model_verbose_name_plural }}.

{% include "main/_list_common.md" %}

{% if new_in_13 %}> _New in AWX 1.3_{% endif %}
