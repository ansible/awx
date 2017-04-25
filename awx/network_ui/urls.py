from django.conf.urls import include, url
import sys

from . import views
import network_ui.routing

app_name = 'network_ui'
urlpatterns = [
        url(r'^$', views.index, name='index'),
]

