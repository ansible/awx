{% ifmeth GET %}
# Retrieve {{ model_verbose_name|title }} Variable Data:

Make a GET request to this resource to retrieve all variables defined for a
{{ model_verbose_name }}.
{% endifmeth %}

{% ifmeth PUT PATCH %}
# Update {{ model_verbose_name|title }} Variable Data:

Make a PUT or PATCH request to this resource to update variables defined for a
{{ model_verbose_name }}.
{% endifmeth %}
