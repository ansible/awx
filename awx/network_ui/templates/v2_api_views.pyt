from rest_framework import viewsets
{%for model in models%}{%if model.api%}
from {{app}}.models import {{model.name}}{%endif%}{%endfor%}
{%for model in models%}{%if model.api%}
from {{app}}.v2_api_serializers import {{model.name}}Serializer{%endif%}{%endfor%}

{%for model in models%}{%if model.api%}



class {{model.name}}ViewSet(viewsets.ModelViewSet):

    queryset = {{model.name}}.objects.all()
    serializer_class = {{model.name}}Serializer
    {%if model.v2_lookup_field-%}
    lookup_field = '{{model.v2_lookup_field}}'
    {%-endif%}

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
	response = super({{model.name}}ViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
	response = super({{model.name}}ViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
	response = super({{model.name}}ViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
	response = super({{model.name}}ViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
	response = super({{model.name}}ViewSet, self).destroy(request, *args, **kwargs)
        return response

{%endif%}{%endfor%}
