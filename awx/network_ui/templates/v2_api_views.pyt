import json
import channels
from utils import transform_dict

from awx.api.generics import ListCreateAPIView
from awx.api.generics import RetrieveUpdateDestroyAPIView
from {{app}}.models import ({%for model in models%}{%if model.api%}{{model.name}},
                            {%endif%}{%endfor%})
from {{app}}.v2_api_serializers import ({%for model in models%}{%if model.api%}{{model.name}}Serializer,
                                        {%endif%}{%endfor%})

{%for model in models%}{%if model.api%}


class {{model.name}}List(ListCreateAPIView):

    model = {{model.name}}
    serializer_class = {{model.name}}Serializer

    def create(self, request, *args, **kwargs):
	response = super({{model.name}}List, self).create(request, *args, **kwargs)
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

class {{model.name}}Detail(RetrieveUpdateDestroyAPIView):

    model = {{model.name}}
    serializer_class = {{model.name}}Serializer

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

	return super({{model.name}}Detail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
	return super({{model.name}}Detail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
	return super({{model.name}}Detail, self).destroy(request, pk, *args, **kwargs)

{%endif%}{%endfor%}
