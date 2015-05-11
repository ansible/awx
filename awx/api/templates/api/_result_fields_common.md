{% for fn, fm in serializer_fields.items %}{% spaceless %}
{% if not write_only or not fm.read_only %}
* `{{ fn }}`: {{ fm.help_text|capfirst }} ({{ fm.type }}{% if write_only and fm.required %}, required{% endif %}{% if write_only and fm.read_only %}, read-only{% endif %}{% if write_only and not fm.choices and not fm.required %}, default=`{% if fm.type == "string" or fm.type == "email" %}"{% firstof fm.default "" %}"{% else %}{{ fm.default }}{% endif %}`{% endif %}){% if fm.choices %}{% for c in fm.choices %}
    - `{% if c.0 == "" %}""{% else %}{{ c.0 }}{% endif %}`{% if c.1 != c.0 %}: {{ c.1 }}{% endif %}{% if write_only and c.0 == fm.default %} (default){% endif %}{% endfor %}{% endif %}{% endif %}
{% endspaceless %}
{% endfor %}
