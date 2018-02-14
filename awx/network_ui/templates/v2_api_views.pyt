from awx.api.generics import ListCreateAPIView
from awx.api.generics import RetrieveUpdateDestroyAPIView
{%for model in models%}{%if model.api%}
from {{app}}.models import {{model.name}}{%endif%}{%endfor%}
{%for model in models%}{%if model.api%}
from {{app}}.v2_api_serializers import {{model.name}}Serializer{%endif%}{%endfor%}

{%for model in models%}{%if model.api%}


class {{model.name}}List(ListCreateAPIView):

    model = {{model.name}}
    serializer_class = {{model.name}}Serializer


class {{model.name}}Detail(RetrieveUpdateDestroyAPIView):

    model = {{model.name}}
    serializer_class = {{model.name}}Serializer

{%endif%}{%endfor%}
