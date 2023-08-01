from django.urls import re_path

from awx.api.generics import LoggedLoginView

extend_urls = [
    re_path(r'^login/$', LoggedLoginView.as_view(template_name='rest_framework/login.html', extra_context={'inside_login_context': True}), name='login'),
]
