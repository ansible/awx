from django.conf.urls import url
from django.views.generic.base import TemplateView


class IndexView(TemplateView):

    template_name = 'index.html'


app_name = 'ui_next'

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    #url(r'^migrations_notran/$', migrations_notran, name='migrations_notran'),
]
