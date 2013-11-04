{% for fn, fm in serializer_fields.items %}{% spaceless %}
{% if not write_only or not fm.read_only %}
* `{{ fn }}`: {{ fm.help_text|capfirst }} ({{ fm.type }}{% if fm.required %}, required{% endif %}{% if fm.read_only %}, read-only{% endif %})
{% endif %}
{% endspaceless %}
{% endfor %}
