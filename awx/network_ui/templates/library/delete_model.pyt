{%for model in models-%}
{%-if model.api-%}
#---- delete_{{model.name.lower()}}
{%endif%}
{%endfor%}
