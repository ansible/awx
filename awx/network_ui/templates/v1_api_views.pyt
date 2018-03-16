import channels
import json
from rest_framework import viewsets
from utils import transform_dict
{%for model in models%}{%if model.api%}
from {{app}}.models import {{model.name}}{%endif%}{%endfor%}
{%for model in models%}{%if model.api%}
from {{app}}.v1_api_serializers import {{model.name}}Serializer{%endif%}{%endfor%}

{%for model in models%}{%if model.api%}


class {{model.name}}ViewSet(viewsets.ModelViewSet):

    queryset = {{model.name}}.objects.all()
    serializer_class = {{model.name}}Serializer

    def create(self, request, *args, **kwargs):
	response = super({{model.name}}ViewSet, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['{%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}']
        message = dict()
        {%if model.create_transform%}
        message.update(transform_dict({ {% for key, value in model.create_transform.iteritems()%} '{{key}}':'{{value}}',
                                       {%endfor%} },{{model.name}}.objects.filter(pk=pk).values(*[{% for key in model.create_transform.keys()%}'{{key}}',
                                                                                                  {%endfor%}])[0]))
        {%else%}
        message.update(response.data)
        {%endif%}
        message['msg_type'] = "{{model.name}}Create"
        message['{%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}'] = pk
        message['sender'] = 0
        {%if model.topology_id_query %}
        print "sending to topologies", {{model.name}}.objects.filter(pk=pk).values_list('{{model.topology_id_query}}', flat=True)
        for topology_id in {{model.name}}.objects.filter(pk=pk).values_list('{{model.topology_id_query}}', flat=True):
        {%else%}
        print "sending to all topologies"
        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):
        {%endif%}
            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "{{model.name}}Update"
        message['{%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}'] = pk
        message['sender'] = 0
        {%if model.topology_id_query %}
        for topology_id in {{model.name}}.objects.filter(pk=pk).values_list('{{model.topology_id_query}}', flat=True):
        {%else%}
        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):
        {%endif%}
            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

	return super({{model.name}}ViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
	return super({{model.name}}ViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
	return super({{model.name}}ViewSet, self).destroy(request, pk, *args, **kwargs)

{%endif%}{%endfor%}
