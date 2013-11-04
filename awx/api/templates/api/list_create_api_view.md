{% include "api/list_api_view.md" %}

# Create {{ model_verbose_name_plural|title }}:

Make a POST request to this resource with the following {{ model_verbose_name }}
fields to create a new {{ model_verbose_name }}:

{% with write_only=1 %}
{% include "api/_result_fields_common.md" %}
{% endwith %}

{% include "api/_new_in_awx.md" %}
