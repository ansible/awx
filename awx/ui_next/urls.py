from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from awx.main.utils.common import get_licenser


class IndexView(TemplateView):

    template_name = 'index.html'


class MigrationsNotran(TemplateView):

    template_name = 'installing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_name = get_licenser().validate()['product_name']
        context['title'] = _('%s Upgrading' % product_name)
        context['image_alt'] = _('Logo')
        context['aria_spinner'] = _('Loading')
        context['message_upgrade'] = _('%s is currently upgrading.' % product_name)
        context['message_refresh'] = _('This page will refresh when complete.')
        return context


app_name = 'ui_next'

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^migrations_notran/$', MigrationsNotran.as_view(), name='migrations_notran'),
]
