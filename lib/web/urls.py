from django.conf.urls import patterns, url
from lib.web.views import IndexView

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
)
