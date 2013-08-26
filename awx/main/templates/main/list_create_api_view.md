{% include "main/list_api_view.md" %}

# Create {{ model_verbose_name_plural|title }}:

Make a POST request to this resource with the following {{ model_verbose_name }}
fields to create a new {{ model_verbose_name }}:

{% with write_only=1 %}
{% include "main/_result_fields_common.md" %}
{% endwith %}

{% include "main/_new_in_awx.md" %}
