from django.contrib import admin
{%for model in models%}
from {{app}}.models import {{model.name}}
{%endfor%}

{%for model in models%}
class {{model.name}}Admin(admin.ModelAdmin):
    fields = ({%for field in model.fields%}{%if not field.pk%}'{{field.name}}',{%endif%}{%endfor%})
    raw_id_fields = ({%for field in model.fields%}{%if field.ref%}'{{field.name}}',{%endif%}{%endfor%})
admin.site.register({{model.name}}, {{model.name}}Admin)
{%endfor%}

