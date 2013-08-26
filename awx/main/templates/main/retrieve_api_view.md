# Retrieve {{ model_verbose_name|title }}:

Make GET request to this resource to retrieve a single {{ model_verbose_name }}
record containing the following fields:

{% include "main/_result_fields_common.md" %}

{% if new_in_13 %}> _New in AWX 1.3_{% endif %}

