

from collections import namedtuple


{%for model in models%}
{{model.name}} = namedtuple('{{model.name}}',[{%for field in model.fields%}{%if field.pk%}'{{field.name}}'{%endif%}{%endfor%},
                                              {%for field in model.fields%}{%if not field.pk%}'{{field.name}}',
                                              {%endif%}{%endfor%}])
{%endfor%}
