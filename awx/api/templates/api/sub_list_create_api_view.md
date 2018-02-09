{% include "api/sub_list_api_view.md" %}

# Create {{ model_verbose_name|title|anora }} for {{ parent_model_verbose_name|title|anora }}:

Make a POST request to this resource with the following {{ model_verbose_name }}
fields to create a new {{ model_verbose_name }} associated with this
{{ parent_model_verbose_name }}.

{% with write_only=1 %}
{% include "api/_result_fields_common.md" %}
{% endwith %}

{% block post_create %}{% endblock %}

{% if has_attach|default:False %}
{% if parent_key %}
# Remove {{ parent_model_verbose_name|title }} {{ model_verbose_name_plural|title }}:

Make a POST request to this resource with `id` and `disassociate` fields to
delete the associated {{ model_verbose_name }}.

    {
        "id": 123,
        "disassociate": true
    }

{% else %}
# Add {{ model_verbose_name_plural|title }} for {{ parent_model_verbose_name|title|anora }}:

Make a POST request to this resource with only an `id` field to associate an
existing {{ model_verbose_name }} with this {{ parent_model_verbose_name }}.

# Remove {{ model_verbose_name_plural|title }} from this {{ parent_model_verbose_name|title }}:

Make a POST request to this resource with `id` and `disassociate` fields to
remove the {{ model_verbose_name }} from this {{ parent_model_verbose_name }}
{% if model_verbose_name != "label" %} without deleting the {{ model_verbose_name }}{% endif %}.
{% endif %}
{% endif %}
