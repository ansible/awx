from rest_framework import serializers
{%for model in models%}{%if model.api%}
from {{app}}.models import {{model.name}}{%endif%}{%endfor%}


{%for model in models%}{%if model.api%}



class {{model.name}}Serializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:{{model.name.lower()}}-detail", lookup_field='pk')
    {%for field in model.fields%}
    {%if field.ref_field%}
    {{field.name}} = serializers.HyperlinkedRelatedField(view_name="network_ui:{{field.ref.lower()}}-detail", lookup_field="pk", read_only=True)
    {%endif%}
    {%endfor%}
    class Meta:
        model = {{model.name}}
        fields = ('url', {%for field in model.fields%}'{{field.name}}',{%endfor%})
{%endif%}{%endfor%}
