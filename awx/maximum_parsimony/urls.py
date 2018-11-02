from django.conf.urls import url
from . import views

urlpatterns = [
	url('start/', views.start_coverage, name='start'),
	url('stop/', views.stop_coverage, name='stop'),
	url('report/', views.report, name='report'),
	url('clean/', views.clean, name='clean')
    ]
