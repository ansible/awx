from django.urls import re_path
from django.views.generic.base import TemplateView


class IndexView(TemplateView):
    template_name = 'index_awx.html'


app_name = 'ui_next'

urlpatterns = [re_path(r'^$', IndexView.as_view(), name='index')]
