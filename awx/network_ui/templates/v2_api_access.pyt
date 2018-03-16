from awx.main.access import BaseAccess, access_registry
{%for model in models%}{%if model.api%}
from {{app}}.models import {{model.name}}{%endif%}{%endfor%}

{%for model in models%}{%if model.api%}

class {{model.name}}Access(BaseAccess):

    model = {{model.name}}

access_registry[{{model.name}}] = {{model.name}}Access
{%endif%}{%endfor%}


