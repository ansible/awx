from rest_framework import viewsets
{%for model in models%}{%if model.api%}
from {{app}}.models import {{model.name}}{%endif%}{%endfor%}
{%for model in models%}{%if model.api%}
from {{app}}.v2_api_serializers import {{model.name}}Serializer{%endif%}{%endfor%}

{%for model in models%}{%if model.api%}



class {{model.name}}ViewSet(viewsets.ModelViewSet):

    queryset = {{model.name}}.objects.all()
    serializer_class = {{model.name}}Serializer

{%endif%}{%endfor%}
