from django.conf import settings
from django.conf.urls import *

urlpatterns = patterns('lib.ui.views',
    url(r'^$', 'index', name='index'),
)
