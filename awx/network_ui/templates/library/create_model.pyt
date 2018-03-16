{%for model in models-%}
{%-if model.api-%}
#---- create_{{model.name.lower()}}
{%endif%}
{%endfor%}
