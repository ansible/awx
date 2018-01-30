from rest_framework import serializers
{%for model in models%}{%if model.api%}
from {{app}}.models import {{model.name}}{%endif%}{%endfor%}


{%for model in models%}{%if model.api%}



class {{model.name}}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {{model.name}}
        fields = ({%for field in model.fields%}'{{field.name}}',{%endfor%})
{%endif%}{%endfor%}
