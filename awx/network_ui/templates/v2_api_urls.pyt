from django.conf.urls import url
{%for model in models-%}{%if model.api%}
from awx.network_ui.v2_api_views import ({{model.name}}List, {{model.name}}Detail)
{%-endif%}
{%-endfor%}


urls = [];
{%for model in models%}{%if model.api%}

urls += [
    url(r'^{{model.name.lower()}}/$', {{model.name}}List.as_view(), name='canvas_{{model.name.lower()}}_list'),
    url(r'^{{model.name.lower()}}/(?P<pk>[0-9]+)/$', {{model.name}}Detail.as_view(), name='canvas_{{model.name.lower()}}_detail'),
];
{%-endif%}
{%-endfor%}

__all__ = ['urls']
