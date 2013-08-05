{% extends "main/sub_list_create_api_view.md" %}

{% block post_create %}
Any fields not explicitly provided for the new job (except `name` and
`description`) will use the default values from the job template.
{% endblock %}
