from awx.api.serializers import BaseSerializer
{%for model in models%}{%if model.api%}
from {{app}}.models import {{model.name}}{%endif%}{%endfor%}


{%for model in models%}{%if model.api%}



class {{model.name}}Serializer(BaseSerializer):
    class Meta:
        model = {{model.name}}
        fields = ({%for field in model.fields%}'{{field.name}}'{%if not loop.last%},
                  {%endif%}{%endfor%})
{%endif%}{%endfor%}
