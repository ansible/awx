from django.urls import re_path

from awx.api.generics import LoggedLogoutView

extend_urls = [
    re_path(r'^logout/$', LoggedLogoutView.as_view(next_page='/api/', redirect_field_name='next'), name='logout'),
]
