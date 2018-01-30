{%for model in models-%}
{%-if model.api-%}
#---- get_{{model.name.lower()}}
{%endif%}
{%endfor%}
