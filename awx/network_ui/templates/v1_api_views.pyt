from rest_framework import viewsets
{%for model in models%}
from {{app}}.models import {{model.name}}{%endfor%}
{%for model in models%}
from {{app}}.v1_api_serializers import {{model.name}}Serializer{%endfor%}

{%for model in models%}



class {{model.name}}ViewSet(viewsets.ModelViewSet):

    queryset = {{model.name}}.objects.all()
    serializer_class = {{model.name}}Serializer

{%endfor%}
