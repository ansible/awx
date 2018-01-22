from rest_framework import serializers
{%for model in models%}
from {{app}}.models import {{model.name}}{%endfor%}


{%for model in models%}



class {{model.name}}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {{model.name}}
        fields = ({%for field in model.fields%}'{{field.name}}',{%endfor%})
{%endfor%}
