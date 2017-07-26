from django.conf.urls import include, url
import sys

from . import views
import prototype.routing

app_name = 'prototype'
urlpatterns = [
        url(r'^$', views.index, name='index'),
]

