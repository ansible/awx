from django.conf import settings
from django.http import Http404
from django.urls import re_path
from django.views.generic.base import TemplateView


class IndexView(TemplateView):
    template_name = 'index_awx.html'

    def get_context_data(self, **kwargs):
        if settings.UI_NEXT is False:
            raise Http404()

        return super().get_context_data(**kwargs)


app_name = 'ui_next'

urlpatterns = [re_path(r'^$', IndexView.as_view(), name='index')]
