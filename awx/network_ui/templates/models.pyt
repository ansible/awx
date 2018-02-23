from django.db import models


{%for model in models%}
class {{model.name}}(models.Model):

    {%for field in model.fields%}{{field.name}} = models.{{field.type}}({%if field.ref%}'{{field.ref}}',{%endif%}{%if field.pk%}primary_key=True,{%endif%}{%if field.len%}max_length={{field.len}},{%endif%}{%if field.related_name%}related_name='{{field.related_name}}',{%endif%}{%if field.default is defined%}default={{field.default}},{%endif%}{%if field.type == 'CharField'%}blank=True{%endif%})
    {%endfor%}

    {%if model.display%}
    def __unicode__(self):
        return self.{{model.display}}
    {%endif%}

{%endfor%}
