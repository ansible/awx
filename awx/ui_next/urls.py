from django.conf.urls import url
from django.views.generic.base import TemplateView


class IndexView(TemplateView):

    template_name = 'index.html'


class MigrationsNotran(TemplateView):

    template_name = 'installing.html'


app_name = 'ui_next'

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^migrations_notran/$', MigrationsNotran.as_view(), name='migrations_notran'),
]
